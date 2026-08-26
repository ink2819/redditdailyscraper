from collections import Counter

from reddit_scraper import report


def test_render_markdown_and_html_smoke():
    topics_result = {
        "shows": [{"show": "Frieren", "thread_count": 2, "total_comments": 1200,
                    "total_score": 500, "sample_url": "https://www.reddit.com/r/anime/x"}],
        "standalone": [{"title": "Weekly thread", "comments": 42, "score": 10,
                         "url": "https://www.reddit.com/r/anime/y"}],
    }
    ip_counts = Counter({"Frieren": 12, "Chainsaw Man": 3})
    ip_trend = [
        {"ip": "Frieren", "today": 12, "baseline_avg": 2.0, "delta": 10.0,
         "pct_change": 500.0, "days_of_history": 7},
    ]
    candidates = Counter({"Marin Kitagawa": 4})
    meta = {
        "ip_subreddits": ["NovelAi", "StableDiffusion"],
        "trend_window_days": 7,
        "topic_post_count": 100,
        "ip_post_count": 200,
    }

    md = report.render_markdown("2026-08-26", topics_result, ip_counts, ip_trend, candidates, meta)
    assert "Frieren" in md
    assert "Marin Kitagawa" in md
    assert "[Frieren](https://www.reddit.com/r/anime/x)" in md

    html = report.render_html("2026-08-26", md)
    assert "<html>" in html
    assert "<table>" in html
    assert '<a href="https://www.reddit.com/r/anime/x">Frieren</a>' in html
    # no raw markdown link syntax should leak into the HTML output
    assert "](http" not in html


def test_render_handles_empty_results():
    topics_result = {"shows": [], "standalone": []}
    meta = {"ip_subreddits": [], "trend_window_days": 7, "topic_post_count": 0, "ip_post_count": 0}
    md = report.render_markdown("2026-08-26", topics_result, Counter(), [], Counter(), meta)
    html = report.render_html("2026-08-26", md)
    assert "No episode-discussion" in md
    assert "<html>" in html
