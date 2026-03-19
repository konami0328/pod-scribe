import feedparser
from datetime import datetime, timezone
from typing import Optional


def parse_feed(url: str) -> list[dict]:
    """
    Fetch and parse a single RSS feed.
    Returns a list of episodes, each with title, published date, audio URL, and unique ID.
    """
    feed = feedparser.parse(url)
    episodes = []

    for entry in feed.entries:
        # Extract audio enclosure URL
        audio_url = None
        for enclosure in entry.get("enclosures", []):
            if enclosure.get("type", "").startswith("audio"):
                audio_url = enclosure.get("href") or enclosure.get("url")
                break

        if not audio_url:
            continue

        # Parse published datetime (UTC)
        published = None
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        episodes.append({
            "title": entry.get("title", "untitled"),
            "published": published,
            "audio_url": audio_url,
            "episode_id": entry.get("id") or audio_url,  # unique identifier for tracking
        })

    return episodes


def filter_episodes(
    episodes: list[dict],
    since: Optional[datetime] = None,
    last: Optional[int] = None,
) -> list[dict]:
    """
    Filter episodes by date or count.
    - since: only include episodes published on or after this datetime
    - last: only include the most recent N episodes
    Episodes are sorted newest-first before filtering.
    """
    # Drop episodes with no publish date
    episodes = [e for e in episodes if e["published"]]

    # Sort newest first
    episodes.sort(key=lambda e: e["published"], reverse=True)

    if since:
        episodes = [e for e in episodes if e["published"] >= since]
    if last:
        episodes = episodes[:last]

    return episodes


if __name__ == "__main__":
    import yaml
    import os

    # Load feeds from config.example.yaml
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.example.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    feeds = config["rss"]["feeds"]

    for feed_config in feeds:
        print(f"Fetching feed: {feed_config['name']} ({feed_config['url']})\n")
        episodes = parse_feed(feed_config["url"])
        print(f"Total episodes found: {len(episodes)}")

        # Test --last 3
        recent = filter_episodes(episodes, last=3)
        print(f"\nMost recent 3 episodes:")
        for ep in recent:
            print(f"  [{ep['published'].date()}] {ep['title']}")
            print(f"    audio: {ep['audio_url']}")

        # Test --since
        since_date = datetime(2026, 3, 10, tzinfo=timezone.utc)
        since_episodes = filter_episodes(episodes, since=since_date)
        print(f"\nEpisodes since 2026-03-10: {len(since_episodes)}")
        print("-" * 60)