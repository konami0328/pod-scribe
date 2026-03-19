import os
import yaml
import requests
from tqdm import tqdm
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load configuration from yaml file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_proxies(config: dict) -> dict | None:
    """
    Extract proxy settings from config.
    Returns None if proxy is not configured.
    """
    proxy_config = config.get("proxy", {})
    if proxy_config.get("http"):
        return {
            "http": proxy_config["http"],
            "https": proxy_config["https"],
        }
    return None


def download_audio(episode: dict, output_dir: str, proxies: dict | None = None) -> str:
    """
    Download audio file for a single episode.
    Returns the local file path of the downloaded audio.
    Skips download if file already exists.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize title for use as filename
    safe_title = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_"
        for c in episode["title"]
    ).strip()
    safe_title = safe_title[:80]  # Limit filename length

    # Preserve original file extension (usually .mp3 or .m4a)
    ext = os.path.splitext(episode["audio_url"].split("?")[0])[-1] or ".mp3"
    filename = f"{episode['published'].strftime('%Y%m%d')}_{safe_title}{ext}"
    filepath = os.path.join(output_dir, filename)

    # Skip if already downloaded
    if os.path.exists(filepath):
        print(f"  [skip] Already exists: {filename}")
        return filepath

    print(f"  [download] {filename}")
    response = requests.get(
        episode["audio_url"],
        stream=True,
        timeout=60,
        proxies=proxies,
    )
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    with open(filepath, "wb") as f, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=filename[:40],
    ) as bar:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))

    print(f"  [done] Saved to {filepath}")
    return filepath


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.rss_reader import parse_feed, filter_episodes

    config_path = os.path.join(os.path.dirname(__file__), "..", "config.example.yaml")
    config = load_config(config_path)

    proxies = get_proxies(config)
    output_dir = config["output"]["transcripts_dir"]
    feed_config = config["rss"]["feeds"][0]

    print(f"Fetching: {feed_config['name']}")
    episodes = parse_feed(feed_config["url"])

    # Test: download most recent 1 episode
    recent = filter_episodes(episodes, last=1)
    for ep in recent:
        path = download_audio(ep, output_dir, proxies=proxies)
        print(f"Audio saved: {path}")