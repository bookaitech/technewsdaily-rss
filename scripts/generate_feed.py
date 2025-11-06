#!/usr/bin/env python3
"""
Generate an RSS 2.0 feed (docs/feed.xml) from an episode XML file and existing feed.xml.

Usage:
  python scripts/generate_feed.py

This script uses only the Python standard library so it can run in GitHub Actions
without installing extra packages.
"""
from __future__ import annotations

import glob
import os
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom, Node


REPO_NAME = Path(__file__).resolve().parents[1].name
SITE_TITLE = "TechNewsDaily"
SITE_LINK = "/"
SITE_DESC = "Tech news and summaries — generated RSS feed"


def iso_to_rfc2822(iso: str) -> str:
    # Parse ISO 8601 and output RFC 2822 for RSS pubDate
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt)


def get_latest_episode_file(data_dir: Path) -> Path | None:
    # Find all episode XML files and get the latest one by unix timestamp
    # Check both "episode-" and "eposide-" prefixes due to potential typo
    episode_files = glob.glob(str(data_dir / "[e][p][io]s[io]de-*.xml"))
    if not episode_files:
        return None
    
    # Extract unix timestamps and find the latest
    latest_file = max(episode_files, key=lambda f: int(f.split('-')[-1].split('.')[0]))
    return Path(latest_file)


def merge_episode_into_feed(feed_file: Path, episode_file: Path) -> bytes:
    # Validate episode XML has proper XML declaration and root element
    # If feed file doesn't exist, create a new one
    if not feed_file.exists():
        rss = ET.Element('rss', version='2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = SITE_TITLE
        ET.SubElement(channel, 'link').text = SITE_LINK
        ET.SubElement(channel, 'description').text = SITE_DESC
        ET.SubElement(channel, 'language').text = 'en-us'
    else:
        # Parse existing feed
        rss = ET.parse(feed_file).getroot()
        channel = rss.find('channel')

    # Update build date
    build_date = channel.find('lastBuildDate')
    if build_date is None:
        build_date = ET.SubElement(channel, 'lastBuildDate')
    build_date.text = format_datetime(datetime.now(timezone.utc))

    # Parse new episode from the episode XML file directly. Some sources may
    # produce unescaped '&' characters inside <link> which makes the XML
    # not well-formed. Try a normal parse first; on failure, read the file as
    # text and wrap link contents that contain '&' in CDATA, then parse.
    try:
        episode_tree = ET.parse(episode_file)
    except ET.ParseError:
        text = episode_file.read_text(encoding='utf-8')

        # Replace <link>...&...</link> with CDATA-wrapped content to make it
        # well-formed for parsing. Do not modify if already contains CDATA.
        def _wrap_link_cdata(m: re.Match) -> str:
            open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
            if '<![CDATA[' in inner:
                return f"{open_tag}{inner}{close_tag}"
            return f"{open_tag}<![CDATA[{inner}]]>{close_tag}"

        pattern = re.compile(r"(<link>)(.*?&.*?)(</link>)", flags=re.DOTALL)
        fixed = pattern.sub(_wrap_link_cdata, text)

        episode_tree = ET.ElementTree(ET.fromstring(fixed))

    episode_root = episode_tree.getroot()

    # Extract item from episode XML and insert at the beginning of channel
    new_items = episode_root.findall('.//item')
    existing_items = channel.findall('item')

    # Get existing GUIDs and links to check for duplicates
    existing_guids = set()
    existing_links = set()
    for item in existing_items:
        guid = item.find('guid')
        link = item.find('link')
        if guid is not None and guid.text:
            existing_guids.add(guid.text)
        if link is not None and link.text:
            existing_links.add(link.text)

    # Add only non-duplicate new items
    items_to_keep = []
    for item in new_items:
        guid = item.find('guid')
        link = item.find('link')
        is_duplicate = False
        
        if guid is not None and guid.text:
            if guid.text in existing_guids:
                is_duplicate = True
        elif link is not None and link.text:
            if link.text in existing_links:
                is_duplicate = True
                
        if not is_duplicate:
            items_to_keep.append(item)
            # Add to sets to catch duplicates within new items
            if guid is not None and guid.text:
                existing_guids.add(guid.text)
            if link is not None and link.text:
                existing_links.add(link.text)

    # Clear channel
    for item in existing_items:
        channel.remove(item)

    # Add non-duplicate new items first
    for item in items_to_keep:
        channel.append(item)

    # Add back existing items
    for item in existing_items:
        channel.append(item)

    # Pretty-print, but remove excessive empty lines for compactness
    raw = ET.tostring(rss, encoding='utf-8')
    parsed = minidom.parseString(raw)

    # Replace text nodes for <item>/<link> with CDATA sections so the
    # final serialized feed contains literal '&' inside URLs instead of
    # the escaped '&amp;'. This helps consumers that extract innerHTML
    # or raw text to construct HTTP requests without seeing the entity.
    for link_node in parsed.getElementsByTagName('link'):
        parent = link_node.parentNode
        if parent is None:
            continue
        # Only convert item links, not the channel-level <link>
        if parent.nodeName != 'item':
            continue

        # Collect existing text content (including any CDATA) then remove children
        text_parts = []
        for child in list(link_node.childNodes):
            if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                text_parts.append(child.data)
            link_node.removeChild(child)

        text = ''.join(text_parts)
        cdata = parsed.createCDATASection(text)
        link_node.appendChild(cdata)

    pretty = parsed.toprettyxml(indent='  ', encoding='utf-8')
    # Remove empty lines
    compact = b'\n'.join([line for line in pretty.splitlines() if line.strip()])
    return compact


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / 'data'
    feed_file = repo_root / 'docs' / 'feed.xml'

    # Find the latest episode file
    episode_file = get_latest_episode_file(data_dir)
    if episode_file is None:
        print("No episode file found in data directory")
        return

    # Merge episode into feed
    xml_bytes = merge_episode_into_feed(feed_file, episode_file)

    # Ensure output directory exists
    feed_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write updated feed
    with open(feed_file, 'wb') as f:
        f.write(xml_bytes)

    print(f"Wrote RSS feed to: {feed_file}")


if __name__ == '__main__':
    main()
