import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import tempfile

from scripts.generate_feed import merge_episode_into_feed

class TestGenerateFeed(unittest.TestCase):
    def test_episode_xml_parsing(self):
        # Create a temporary episode file with proper XML structure
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as episode_file:
            episode_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <item>
        <title>TechNewsDaily — Test Episode</title>
        <link>https://example.com/test</link>
        <description>Test episode description</description>
        <pubDate>2025-11-06</pubDate>
        <guid>test-episode-1</guid>
    </item>
</rss>
''')
            episode_path = Path(episode_file.name)

        # Create a temporary feed file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as feed_file:
            feed_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>TechNewsDaily</title>
        <link>/</link>
        <description>Tech news and summaries — generated RSS feed</description>
        <language>en-us</language>
    </channel>
</rss>
''')
            feed_path = Path(feed_file.name)

        try:
            # This should not raise an exception if XML is well-formed
            xml_bytes = merge_episode_into_feed(feed_path, episode_path)
            
            # Verify the output can be parsed
            parsed = ET.fromstring(xml_bytes.decode('utf-8'))
            
            # Check if the new item was merged
            channel = parsed.find('channel')
            self.assertIsNotNone(channel)
            
            items = channel.findall('item')
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].find('title').text, 'TechNewsDaily — Test Episode')
            
        finally:
            # Clean up temporary files
            episode_path.unlink()
            feed_path.unlink()

    def test_invalid_episode_xml(self):
        # Create a temporary episode file with invalid XML structure
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as episode_file:
            episode_file.write('''<item>
      <title>TechNewsDaily — Invalid Episode</title>
      <link>https://example.com/test</link>
      <description>Invalid episode description</description>
      <pubDate>2025-11-06</pubDate>
      <guid>test-episode-invalid</guid>
</item>
''')
            episode_path = Path(episode_file.name)

        try:
            # This should raise an exception due to missing XML declaration and root element
            with self.assertRaises(ET.ParseError):
                merge_episode_into_feed(Path('dummy.xml'), episode_path)
        finally:
            # Clean up temporary file
            episode_path.unlink()

if __name__ == '__main__':
    unittest.main()