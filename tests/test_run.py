import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from run import (
    find_audio_files,
    find_unprocessed,
    match_audio_file,
    match_feeds,
    resolve_feeds,
)


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_feeds():
    return [
        {"name": "Invest Like the Best", "url": "https://feeds.example.com/invest"},
        {"name": "TEDx SHORTS", "url": "https://feeds.example.com/tedx"},
        {"name": "Lex Fridman Podcast", "url": "https://feeds.example.com/lex"},
    ]


@pytest.fixture
def mock_transcripts_dir(tmp_path):
    """Create a temporary directory with sample audio and transcript files."""
    (tmp_path / "20260317_Episode_A.mp3").touch()
    (tmp_path / "20260310_Episode_B.mp3").touch()
    (tmp_path / "20260310_Episode_B.txt").touch()  # already transcribed
    (tmp_path / "20260301_Episode_C.m4a").touch()
    (tmp_path / "notes.txt").touch()               # irrelevant file
    return str(tmp_path)


# ── find_audio_files ─────────────────────────────────────────────────────────

class TestFindAudioFiles:
    def test_returns_only_audio_files(self, mock_transcripts_dir):
        result = find_audio_files(mock_transcripts_dir)
        assert set(result) == {
            "20260317_Episode_A.mp3",
            "20260310_Episode_B.mp3",
            "20260301_Episode_C.m4a",
        }

    def test_ignores_txt_files(self, mock_transcripts_dir):
        result = find_audio_files(mock_transcripts_dir)
        assert "notes.txt" not in result

    def test_empty_directory(self, tmp_path):
        result = find_audio_files(str(tmp_path))
        assert result == []


# ── find_unprocessed ─────────────────────────────────────────────────────────

class TestFindUnprocessed:
    def test_skips_already_transcribed(self, mock_transcripts_dir):
        result = find_unprocessed(mock_transcripts_dir)
        assert "20260310_Episode_B.mp3" not in result

    def test_includes_untranscribed(self, mock_transcripts_dir):
        result = find_unprocessed(mock_transcripts_dir)
        assert "20260317_Episode_A.mp3" in result
        assert "20260301_Episode_C.m4a" in result

    def test_empty_directory(self, tmp_path):
        result = find_unprocessed(str(tmp_path))
        assert result == []


# ── match_audio_file ──────────────────────────────────────────────────────────

class TestMatchAudioFile:
    def test_exact_keyword(self, mock_transcripts_dir):
        result = match_audio_file(mock_transcripts_dir, "Episode_A")
        assert result == ["20260317_Episode_A.mp3"]

    def test_case_insensitive(self, mock_transcripts_dir):
        result = match_audio_file(mock_transcripts_dir, "episode_a")
        assert result == ["20260317_Episode_A.mp3"]

    def test_partial_match(self, mock_transcripts_dir):
        result = match_audio_file(mock_transcripts_dir, "Episode")
        assert len(result) == 3

    def test_no_match(self, mock_transcripts_dir):
        result = match_audio_file(mock_transcripts_dir, "nonexistent")
        assert result == []


# ── match_feeds ───────────────────────────────────────────────────────────────

class TestMatchFeeds:
    def test_exact_match(self, sample_feeds):
        result = match_feeds(sample_feeds, "TEDx SHORTS")
        assert len(result) == 1
        assert result[0]["name"] == "TEDx SHORTS"

    def test_partial_match(self, sample_feeds):
        result = match_feeds(sample_feeds, "Invest")
        assert len(result) == 1
        assert result[0]["name"] == "Invest Like the Best"

    def test_case_insensitive(self, sample_feeds):
        result = match_feeds(sample_feeds, "tedx")
        assert len(result) == 1

    def test_no_match(self, sample_feeds):
        result = match_feeds(sample_feeds, "nonexistent")
        assert result == []

    def test_multiple_matches(self, sample_feeds):
        # "podcast" doesn't appear in any name, but "e" appears in all
        result = match_feeds(sample_feeds, "e")
        assert len(result) == 3


# ── resolve_feeds ─────────────────────────────────────────────────────────────

class TestResolveFeeds:
    def test_all_returns_all_feeds(self, sample_feeds):
        result = resolve_feeds(sample_feeds, "all")
        assert result == sample_feeds

    def test_keyword_returns_single_match(self, sample_feeds):
        result = resolve_feeds(sample_feeds, "TEDx")
        assert len(result) == 1
        assert result[0]["name"] == "TEDx SHORTS"

    def test_no_match_exits(self, sample_feeds):
        with pytest.raises(SystemExit):
            resolve_feeds(sample_feeds, "nonexistent")

    def test_multiple_matches_exits(self, sample_feeds):
        # "Fridman" only matches Lex, but "Like" only matches Invest
        # Use a keyword that genuinely appears in multiple names
        # "i" appears in "Invest Like the Best", "TEDx SHORTS" (no), "Lex Fridman" (no)
        # Simplest: add a predictable ambiguous case
        feeds = [
            {"name": "Python Podcast", "url": "https://example.com/python"},
            {"name": "Python Weekly", "url": "https://example.com/weekly"},
        ]
        with pytest.raises(SystemExit):
            resolve_feeds(feeds, "Python")


# ── rss_reader ────────────────────────────────────────────────────────────────

class TestFilterEpisodes:
    """Unit tests for filter_episodes logic without hitting real RSS."""

    @pytest.fixture
    def sample_episodes(self):
        return [
            {
                "title": "Episode A",
                "published": datetime(2026, 3, 17, tzinfo=timezone.utc),
                "audio_url": "https://example.com/a.mp3",
                "episode_id": "id_a",
            },
            {
                "title": "Episode B",
                "published": datetime(2026, 3, 10, tzinfo=timezone.utc),
                "audio_url": "https://example.com/b.mp3",
                "episode_id": "id_b",
            },
            {
                "title": "Episode C",
                "published": datetime(2026, 2, 1, tzinfo=timezone.utc),
                "audio_url": "https://example.com/c.mp3",
                "episode_id": "id_c",
            },
        ]

    def test_filter_by_last(self, sample_episodes):
        from src.rss_reader import filter_episodes
        result = filter_episodes(sample_episodes, last=2)
        assert len(result) == 2
        assert result[0]["title"] == "Episode A"  # newest first

    def test_filter_by_since(self, sample_episodes):
        from src.rss_reader import filter_episodes
        since = datetime(2026, 3, 10, tzinfo=timezone.utc)
        result = filter_episodes(sample_episodes, since=since)
        assert len(result) == 2
        assert all(e["published"] >= since for e in result)

    def test_filter_since_and_last(self, sample_episodes):
        from src.rss_reader import filter_episodes
        since = datetime(2026, 2, 1, tzinfo=timezone.utc)
        result = filter_episodes(sample_episodes, since=since, last=2)
        assert len(result) == 2

    def test_no_filter_returns_all_sorted(self, sample_episodes):
        from src.rss_reader import filter_episodes
        result = filter_episodes(sample_episodes)
        assert result[0]["published"] >= result[1]["published"]