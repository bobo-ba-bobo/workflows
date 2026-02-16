#!/usr/bin/env python3
"""
VC News to Discord Bot
Fetches VC-related RSS feeds and posts to Discord
"""

import os
import sys
import feedparser
import requests
from datetime import datetime, timedelta
import time

# Discord Webhook URL from environment variable
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# RSS Feeds to monitor - VC focused
FEEDS = [
    {
        'url': 'https://platum.kr/feed',
        'name': '플래텀',
        'emoji': '🇰🇷'
    },
    {
        'url': 'https://rss.buzzsprout.com/850276.rss',
        'name': 'StrictlyVC',
        'emoji': '💼'
    },
    {
        'url': 'https://techcrunch.com/tag/venture-capital/feed/',
        'name': 'TC: VC',
        'emoji': '💰'
    },
    {
        'url': 'https://feeds.feedburner.com/venturebeat/SZYF',
        'name': 'VentureBeat',
        'emoji': '🚀'
    }
]

def send_to_discord(message):
    """Send message to Discord via webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL not set")
        return False

    data = {
        "content": message
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print(f"✅ Sent: {message[:50]}...")
            return True
        else:
            print(f"❌ Failed to send. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Discord: {e}")
        return False

def is_recent(entry, hours=24):
    """Check if entry was published within the last N hours"""
    try:
        # Try different date fields
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        if not published:
            return True  # If no date, assume it's recent

        entry_time = datetime(*published[:6])
        now = datetime.utcnow()

        return (now - entry_time) < timedelta(hours=hours)
    except:
        return True  # If parsing fails, include it

def fetch_feed(feed_config):
    """Fetch and parse RSS feed"""
    print(f"\n📡 Fetching {feed_config['name']}...")

    try:
        feed = feedparser.parse(feed_config['url'])

        if feed.bozo:
            print(f"⚠️  Warning: Feed may have issues")

        new_items = []
        for entry in feed.entries[:10]:  # Only check latest 10 items
            if is_recent(entry, hours=24):
                title = entry.get('title', 'No title')
                link = entry.get('link', '')

                message = f"{feed_config['emoji']} **{feed_config['name']}** | {title}\n{link}"
                new_items.append(message)

        print(f"Found {len(new_items)} recent items")
        return new_items

    except Exception as e:
        print(f"❌ Error fetching {feed_config['name']}: {e}")
        return []

def main():
    """Main function"""
    print("=" * 50)
    print("💼 VC News to Discord Bot Starting...")
    print(f"⏰ Time: {datetime.utcnow().isoformat()}")
    print("=" * 50)

    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not set!")
        sys.exit(1)

    all_messages = []

    # Fetch all feeds
    for feed_config in FEEDS:
        items = fetch_feed(feed_config)
        all_messages.extend(items)
        time.sleep(1)  # Be nice to servers

    # Send to Discord
    if all_messages:
        print(f"\n📤 Sending {len(all_messages)} items to Discord...")

        for message in all_messages[:15]:  # Limit to 15 items to avoid spam
            send_to_discord(message)
            time.sleep(2)  # Discord rate limit: ~5 messages per second
    else:
        print("\n📭 No new items found")

    print("\n✅ Bot finished!")
    print("=" * 50)

if __name__ == "__main__":
    main()
