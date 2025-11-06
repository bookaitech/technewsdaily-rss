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
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom


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
    episode_files = glob.glob(str(data_dir / "episode-*.xml"))
    if not episode_files:
        return None
    
    # Extract unix timestamps and find the latest
    latest_file = max(episode_files, key=lambda f: int(f.split('-')[-1].split('.')[0]))
    return Path(latest_file)


def merge_episode_into_feed(feed_file: Path, episode_file: Path) -> bytes:
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

    # Parse new episode
    episode_tree = ET.parse(episode_file)
    episode_root = episode_tree.getroot()
    
    # Extract item from episode XML and insert at the beginning of channel
    new_items = episode_root.findall('.//item')
    existing_items = channel.findall('item')
    
    # Remove existing items temporarily
    for item in existing_items:
        channel.remove(item)
    
    # Add new items first
    for item in new_items:
        channel.append(item)
    
    # Add back existing items
    for item in existing_items:
        channel.append(item)

    # Pretty-print
    raw = ET.tostring(rss, encoding='utf-8')
    parsed = minidom.parseString(raw)
    pretty = parsed.toprettyxml(indent='  ', encoding='utf-8')
    return pretty


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
    
    # Delete the processed episode file
    episode_file.unlink()
    print(f"Deleted processed episode file: {episode_file}")


if __name__ == '__main__':
    main()
