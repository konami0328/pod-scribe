import os
import sys
import argparse
import yaml
from datetime import datetime, timezone


def load_config(config_path: str) -> dict:
    """Load configuration from yaml file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def find_audio_files(transcripts_dir: str) -> list[str]:
    """Return all audio files in transcripts directory."""
    exts = (".mp3", ".m4a", ".wav")
    return [
        f for f in os.listdir(transcripts_dir)
        if f.endswith(exts)
    ]


def find_unprocessed(transcripts_dir: str) -> list[str]:
    """
    Return audio files that have no corresponding .txt transcript.
    """
    audio_files = find_audio_files(transcripts_dir)
    return [
        f for f in audio_files
        if not os.path.exists(
            os.path.join(transcripts_dir, os.path.splitext(f)[0] + ".txt")
        )
    ]


def match_audio_file(transcripts_dir: str, keyword: str) -> list[str]:
    """
    Match audio files by keyword (case-insensitive).
    Returns list of matching filenames.
    """
    audio_files = find_audio_files(transcripts_dir)
    keyword_lower = keyword.lower()
    return [f for f in audio_files if keyword_lower in f.lower()]


def match_feeds(feeds: list[dict], keyword: str) -> list[dict]:
    """
    Match feeds by keyword (case-insensitive) against feed name.
    Returns list of matching feed configs.
    """
    keyword_lower = keyword.lower()
    return [f for f in feeds if keyword_lower in f["name"].lower()]


def resolve_feeds(feeds: list[dict], pod: str) -> list[dict]:
    """
    Resolve which feeds to process based on --pod argument.
    - "all": return all feeds
    - keyword: fuzzy match against feed names
    """
    if pod.lower() == "all":
        return feeds

    matches = match_feeds(feeds, pod)
    if not matches:
        print(f"No podcast found matching: '{pod}'")
        print("Available podcasts:")
        for f in feeds:
            print(f"  - {f['name']}")
        sys.exit(1)
    if len(matches) > 1:
        print(f"Multiple podcasts matched '{pod}':")
        for f in matches:
            print(f"  - {f['name']}")
        print("Please be more specific.")
        sys.exit(1)

    return matches


def run_download(
    config: dict,
    feeds: list[dict],
    since: datetime | None,
    last: int | None,
    keyword: str | None,
) -> None:
    """
    Download episodes from the given feeds.
    - since/last: filter by date or count
    - keyword: fuzzy match episode title (overrides since/last)
    """
    from src.rss_reader import parse_feed, filter_episodes
    from src.downloader import download_audio, get_proxies

    proxies = get_proxies(config)
    output_dir = config["output"]["transcripts_dir"]

    for feed_config in feeds:
        print(f"\nFetching: {feed_config['name']}")
        episodes = parse_feed(feed_config["url"])

        if keyword:
            # Fuzzy match against episode titles
            keyword_lower = keyword.lower()
            filtered = [e for e in episodes if keyword_lower in e["title"].lower()]
            if since:
                filtered = [e for e in filtered if e["published"] >= since]
            if last:
                filtered = filtered[:last]
            if not filtered:
                print(f"  No episodes found matching: '{keyword}'")
                continue
            if len(filtered) > 1:
                print(f"  Multiple episodes matched '{keyword}':")
                for e in filtered:
                    print(f"    [{e['published'].date()}] {e['title']}")
                print("  Please be more specific.")
                continue
        else:
            filtered = filter_episodes(episodes, since=since, last=last)

        if not filtered:
            print("  No episodes matched the given filters.")
            continue

        print(f"  {len(filtered)} episode(s) to download.")
        for ep in filtered:
            download_audio(ep, output_dir, proxies=proxies)


def run_transcribe(config: dict, keyword: str | None) -> None:
    """
    Transcribe audio files.
    - keyword provided: transcribe matched file(s)
    - no keyword: transcribe all audio files without a transcript
    """
    from src.transcriber import load_model, transcribe_audio, save_transcript

    output_dir = config["output"]["transcripts_dir"]
    model_size = config["whisper"]["model"]
    language = config["whisper"]["language"]

    if keyword:
        matches = match_audio_file(output_dir, keyword)
        if not matches:
            print(f"No audio file found matching: '{keyword}'")
            sys.exit(1)
        if len(matches) > 1:
            print(f"Multiple matches found for '{keyword}':")
            for m in matches:
                print(f"  {m}")
            print("Please be more specific.")
            sys.exit(1)
        targets = matches
    else:
        targets = find_unprocessed(output_dir)
        if not targets:
            print("No unprocessed audio files found.")
            return

    print(f"\n{len(targets)} file(s) to transcribe.")
    model = load_model(model_size)

    for filename in targets:
        audio_path = os.path.join(output_dir, filename)
        transcript = transcribe_audio(model, audio_path, language=language)
        save_transcript(transcript, audio_path, output_dir)


def parse_args():
    parser = argparse.ArgumentParser(
        description="pod-scribe: download and transcribe podcast episodes"
    )
    parser.add_argument(
        "--pod", type=str, default="all",
        help="Podcast name to process (fuzzy match). Use 'all' for all feeds (default: all)"
    )
    parser.add_argument("--download", nargs="?", const="", metavar="KEYWORD",
                        help="Download episodes. Optional keyword to match specific episode title.")
    parser.add_argument("--transcribe", nargs="?", const="", metavar="KEYWORD",
                        help="Transcribe episodes. Optional keyword to match specific audio file.")
    parser.add_argument("--since", type=str, help="Download episodes since date (YYYY-MM-DD)")
    parser.add_argument("--last", type=int, help="Download only the most recent N episodes")
    parser.add_argument("--config", type=str, default="config.yaml",
                        help="Path to config file (default: config.yaml)")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.download is None and args.transcribe is None:
        print("Please specify --download and/or --transcribe.")
        print("Examples:")
        print("  python run.py --download --since 2026-03-10")
        print("  python run.py --download --last 3")
        print("  python run.py --download 'stock'")
        print("  python run.py --pod 'Invest Like the Best' --download --last 3")
        print("  python run.py --transcribe")
        print("  python run.py --transcribe 'stock'")
        print("  python run.py --download --transcribe --last 3")
        sys.exit(1)

    config = load_config(args.config)
    feeds = resolve_feeds(config["rss"]["feeds"], args.pod)

    # Parse --since date
    since = None
    if args.since:
        since = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if args.download is not None:
        keyword = args.download if args.download else None
        run_download(config, feeds, since=since, last=args.last, keyword=keyword)

    if args.transcribe is not None:
        keyword = args.transcribe if args.transcribe else None
        run_transcribe(config, keyword=keyword)


if __name__ == "__main__":
    main()