#!/usr/bin/env python3
"""
Generate an RSS 2.0 feed (docs/feed.xml) from data/posts.json.

Usage:
  python scripts/generate_feed.py

This script uses only the Python standard library so it can run in GitHub Actions
without installing extra packages.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from pathlib import Path


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


def build_rss(items: list[dict]) -> bytes:
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')

    SubElement(channel, 'title').text = SITE_TITLE
    SubElement(channel, 'link').text = SITE_LINK
    SubElement(channel, 'description').text = SITE_DESC
    SubElement(channel, 'lastBuildDate').text = format_datetime(datetime.now(timezone.utc))
    SubElement(channel, 'language').text = 'en-us'

    for it in items:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = it.get('title')
        SubElement(item, 'link').text = it.get('link')
        SubElement(item, 'description').text = it.get('description')
        pub = it.get('pubDate')
        if pub:
            SubElement(item, 'pubDate').text = iso_to_rfc2822(pub)
        guid = it.get('guid') or it.get('link')
        SubElement(item, 'guid').text = guid

    # Pretty-print
    raw = tostring(rss, encoding='utf-8')
    parsed = minidom.parseString(raw)
    pretty = parsed.toprettyxml(indent='  ', encoding='utf-8')
    return pretty


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_file = repo_root / 'data' / 'posts.json'
    out_file = repo_root / 'docs' / 'feed.xml'

    if not data_file.exists():
        raise SystemExit(f"Missing posts data file: {data_file}")

    with open(data_file, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # Sort descending by pubDate (newest first)
    def parse_iso(x):
        return datetime.fromisoformat(x['pubDate']) if x.get('pubDate') else datetime.min

    items = sorted(items, key=parse_iso, reverse=True)

    xml_bytes = build_rss(items)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'wb') as f:
        f.write(xml_bytes)

    print(f"Wrote RSS feed to: {out_file}")


if __name__ == '__main__':
    main()
