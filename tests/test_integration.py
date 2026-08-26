"""End-to-end smoke test wiring main.run() together without touching the network."""

import main
from reddit_scraper.client import RedditClient

ANIME_POSTS = [
    {"title": "Frieren: Beyond Journey's End - Episode 1 discussion",
     "num_comments": 800, "score": 400, "permalink": "/r/anime/comments/1/"},
    {"title": "Frieren: Beyond Journey's End - Episode 2 discussion",
     "num_comments": 900, "score": 450, "permalink": "/r/anime/comments/2/"},
    {"title": "Weekly discussion thread", "num_comments": 30, "score": 5,
     "permalink": "/r/anime/comments/3/"},
]

AI_ANIME_POSTS = [
    {"title": "Frieren LoRA render, feedback welcome", "link_flair_text": "Artwork",
     "num_comments": 10, "score": 50, "permalink": "/r/NovelAi/comments/4/"},
    {"title": "Marin Kitagawa cosplay AI render", "link_flair_text": "Artwork",
     "num_comments": 5, "score": 20, "permalink": "/r/NovelAi/comments/5/"},
]


def test_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(main.config, "REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setattr(main.config, "HISTORY_DIR", str(tmp_path / "history"))
    monkeypatch.setenv("REDDIT_CLIENT_ID", "test")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test")

    def fake_fetch_listing(self, subreddit, sort="top", time_filter=None, limit=200):
        return ANIME_POSTS if subreddit == "anime" else AI_ANIME_POSTS

    monkeypatch.setattr(RedditClient, "fetch_listing", fake_fetch_listing)

    md_path, html_path = main.run("2026-08-26")

    assert md_path.exists()
    assert html_path.exists()
    md_text = md_path.read_text()
    assert "Frieren: Beyond Journey's End" in md_text
    assert "Frieren" in md_text  # IP mention section
    assert "Marin Kitagawa" in md_text  # candidate section
