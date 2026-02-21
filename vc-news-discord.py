#!/usr/bin/env python3
"""
VC News to Discord Bot
Fetches VC-related RSS feeds and posts to Discord
"""

import os
import sys
import json
import feedparser
import requests
from datetime import datetime, timedelta
import time
from anthropic import Anthropic

# Discord Webhook URL from environment variable
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')

SEEN_ITEMS_FILE = 'seen_vc_news.json'
SEEN_ITEMS_MAX_AGE_DAYS = 14  # Clean up entries older than 14 days

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

def load_seen_items():
    """Load previously seen items from JSON file"""
    try:
        with open(SEEN_ITEMS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_seen_items(seen):
    """Save seen items to JSON file, cleaning up old entries"""
    cutoff = (datetime.utcnow() - timedelta(days=SEEN_ITEMS_MAX_AGE_DAYS)).isoformat()
    cleaned = {k: v for k, v in seen.items() if v >= cutoff}
    with open(SEEN_ITEMS_FILE, 'w') as f:
        json.dump(cleaned, f, indent=2)

def generate_summary(title, description):
    """Generate 3-line summary using Claude API"""
    if not CLAUDE_API_KEY:
        return ""

    try:
        client = Anthropic(api_key=CLAUDE_API_KEY)

        prompt = f"""다음 VC/스타트업 기사를 한국어로 정확히 3줄로 요약해주세요. 각 줄은 한 문장으로.

제목: {title}
내용: {description[:500]}

형식:
• [첫 번째 핵심 내용]
• [두 번째 핵심 내용]
• [세 번째 핵심 내용]"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text.strip()
    except Exception as e:
        print(f"⚠️ Summary generation failed: {e}")
        return ""

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
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        if not published:
            return True  # If no date, assume it's recent

        entry_time = datetime(*published[:6])
        now = datetime.utcnow()

        return (now - entry_time) < timedelta(hours=hours)
    except:
        return True  # If parsing fails, include it

def fetch_feed(feed_config, seen_items):
    """Fetch and parse RSS feed, skipping already-seen items"""
    print(f"\n📡 Fetching {feed_config['name']}...")

    try:
        feed = feedparser.parse(feed_config['url'])

        if feed.bozo:
            print(f"⚠️  Warning: Feed may have issues")

        new_items = []
        for entry in feed.entries[:10]:  # Only check latest 10 items
            link = entry.get('link', '')
            item_id = link or entry.get('id', '')

            if not item_id:
                continue

            # Skip already-seen items
            if item_id in seen_items:
                print(f"  ⏭️  Already sent: {entry.get('title', '')[:50]}")
                continue

            if is_recent(entry, hours=24):
                title = entry.get('title', 'No title')
                description = entry.get('summary', '') or entry.get('description', '')

                # Generate summary
                summary = generate_summary(title, description)

                message = f"{feed_config['emoji']} **{feed_config['name']}** | {title}\n"
                if summary:
                    message += f"{summary}\n"
                message += f"{link}"
                new_items.append((item_id, message))

        print(f"Found {len(new_items)} new items")
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

    seen_items = load_seen_items()
    print(f"📚 Loaded {len(seen_items)} seen items")

    all_messages = []

    # Fetch all feeds
    for feed_config in FEEDS:
        items = fetch_feed(feed_config, seen_items)
        all_messages.extend(items)
        time.sleep(1)  # Be nice to servers

    # Send to Discord
    if all_messages:
        print(f"\n📤 Sending {len(all_messages)} items to Discord...")

        for item_id, message in all_messages[:15]:  # Limit to 15 items to avoid spam
            if send_to_discord(message):
                seen_items[item_id] = datetime.utcnow().isoformat()
            time.sleep(2)  # Discord rate limit: ~5 messages per second
    else:
        print("\n📭 No new items found")

    save_seen_items(seen_items)
    print(f"💾 Saved seen items")

    print("\n✅ Bot finished!")
    print("=" * 50)

if __name__ == "__main__":
    main()
