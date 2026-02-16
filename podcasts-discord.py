#!/usr/bin/env python3
"""
Podcast to Discord Bot
Fetches podcast RSS feeds, generates AI summaries, and posts to Discord
"""

import os
import sys
import json
import feedparser
import requests
from datetime import datetime
from anthropic import Anthropic

# Configuration
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true'
SEEN_EPISODES_FILE = 'seen_episodes.json'

# Podcasts to monitor
PODCASTS = [
    {
        'url': 'https://www.lennysnewsletter.com/feed',
        'name': "Lenny's Podcast",
        'emoji': '🎙️'
    },
    {
        'url': 'http://thetwentyminutevc.libsyn.com/rss',
        'name': '20VC',
        'emoji': '💰'
    },
    {
        'url': 'https://feeds.simplecast.com/JGE3yC0V',
        'name': 'a16z Podcast',
        'emoji': '🚀'
    },
    {
        'url': 'https://feeds.transistor.fm/acquired',
        'name': 'Acquired',
        'emoji': '📈'
    }
]

def load_seen_episodes():
    """Load previously seen episodes from JSON file"""
    try:
        with open(SEEN_EPISODES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_seen_episodes(seen):
    """Save seen episodes to JSON file"""
    with open(SEEN_EPISODES_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def generate_summary(title, description, show_name):
    """Generate summary using Claude API"""
    if not CLAUDE_API_KEY:
        return "⚠️ Claude API key not configured"

    try:
        client = Anthropic(api_key=CLAUDE_API_KEY)

        prompt = f"""Analyze this podcast episode and provide a detailed summary in bullet points.

Podcast: {show_name}
Title: {title}

Description/Show Notes:
{description[:3000]}

Please provide:
1. 📌 Main topic (1-2 sentences)
2. 🔑 Key points (4-6 detailed bullet points)
3. 💡 Key insights/takeaways (2-3 bullet points)

Format everything with bullet points, be specific and detailed. Write in Korean."""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return f"⚠️ Summary generation failed: {str(e)}"

def send_to_discord(content):
    """Send message to Discord via webhook"""
    if DRY_RUN:
        print("🧪 DRY RUN - Would send to Discord:")
        print("-" * 50)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 50)
        return True

    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not set")
        return False

    # Discord has a 2000 character limit, so we might need to split
    if len(content) > 1900:
        # Split into chunks
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        for chunk in chunks:
            data = {"content": chunk}
            try:
                response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
                if response.status_code != 204:
                    print(f"⚠️ Discord returned status {response.status_code}")
            except Exception as e:
                print(f"❌ Error sending chunk: {e}")
            import time
            time.sleep(1)  # Rate limit
    else:
        data = {"content": content}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
            if response.status_code == 204:
                print(f"✅ Sent to Discord")
                return True
            else:
                print(f"❌ Failed. Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

def fetch_podcast(podcast_config, seen_episodes):
    """Fetch podcast and find new episodes"""
    print(f"\n📡 Fetching {podcast_config['emoji']} {podcast_config['name']}...")

    try:
        feed = feedparser.parse(podcast_config['url'])

        podcast_key = podcast_config['name']
        if podcast_key not in seen_episodes:
            seen_episodes[podcast_key] = []

        new_episodes = []

        # Check latest 5 episodes
        for entry in feed.entries[:5]:
            episode_id = entry.get('id') or entry.get('link', '')

            # Filter by date - only February 2026 onwards
            pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
            if pub_date:
                from datetime import datetime
                episode_date = datetime(*pub_date[:6])
                if episode_date.year < 2026 or (episode_date.year == 2026 and episode_date.month < 2):
                    continue  # Skip episodes before Feb 2026

            if episode_id not in seen_episodes[podcast_key]:
                title = entry.get('title', 'No title')
                link = entry.get('link', '')
                description = entry.get('summary', '') or entry.get('description', '')
                pub_date = entry.get('published', 'Unknown date')

                print(f"  🆕 New episode: {title}")

                # Generate summary
                print(f"  🤖 Generating summary with Claude...")
                summary = generate_summary(title, description, podcast_config['name'])

                # Format Discord message
                message = f"""
{podcast_config['emoji']} **{podcast_config['name']}** - New Episode!

**{title}**

{summary}

🔗 {link}
📅 {pub_date}
"""

                new_episodes.append({
                    'id': episode_id,
                    'message': message
                })

                # Mark as seen
                seen_episodes[podcast_key].append(episode_id)

        if not new_episodes:
            print(f"  📭 No new episodes")

        return new_episodes

    except Exception as e:
        print(f"❌ Error fetching {podcast_config['name']}: {e}")
        return []

def main():
    """Main function"""
    print("=" * 60)
    print("🎙️ Podcast to Discord Bot Starting...")
    print(f"⏰ Time: {datetime.utcnow().isoformat()}")
    if DRY_RUN:
        print("🧪 DRY RUN MODE - Will NOT send to Discord")
    print("=" * 60)

    if not DISCORD_WEBHOOK_URL and not DRY_RUN:
        print("❌ DISCORD_WEBHOOK_URL not set!")
        sys.exit(1)

    if not CLAUDE_API_KEY:
        print("❌ CLAUDE_API_KEY not set!")
        sys.exit(1)

    # Load seen episodes
    seen_episodes = load_seen_episodes()
    print(f"📚 Loaded {len(seen_episodes)} podcast histories")

    all_new_episodes = []

    # Fetch all podcasts
    for podcast in PODCASTS:
        episodes = fetch_podcast(podcast, seen_episodes)
        all_new_episodes.extend(episodes)
        import time
        time.sleep(2)  # Be nice to servers

    # Send to Discord
    if all_new_episodes:
        print(f"\n📤 Sending {len(all_new_episodes)} episodes to Discord...")

        for episode in all_new_episodes:
            send_to_discord(episode['message'])
            import time
            time.sleep(3)  # Discord rate limit

        # Save updated seen episodes
        save_seen_episodes(seen_episodes)
        print(f"\n💾 Saved seen episodes")
    else:
        print("\n📭 No new episodes found")

    print("\n✅ Bot finished!")
    print("=" * 60)

if __name__ == "__main__":
    main()
