#!/usr/bin/env python3
"""Daily Reddit report: most-discussed r/anime topics + AI-anime-circle IP trends.

Usage:
    python main.py                 # run for today (UTC), write reports/<date>.md and .html
    python main.py --date 2026-08-25
    python main.py --skip-ip       # only run the r/anime topics section
    python main.py --skip-topics   # only run the AI-anime IP-tracking section
"""

import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

from reddit_scraper import config, ip_tracker, report, topics
from reddit_scraper.client import RedditClient, SubredditUnavailable

FETCH_ERRORS = (SubredditUnavailable, requests.exceptions.RequestException)


def run(date_str, skip_topics=False, skip_ip=False):
    client = RedditClient()

    topics_result = {"shows": [], "standalone": []}
    topic_post_count = 0
    if not skip_topics:
        print(f"Fetching r/{config.TOPIC_SUBREDDITS[0]}...", file=sys.stderr)
        posts = []
        for sub in config.TOPIC_SUBREDDITS:
            try:
                posts.extend(client.fetch_listing(
                    sub, sort="top", time_filter=config.TIME_FILTER,
                    limit=config.POSTS_PER_SUBREDDIT,
                ))
            except FETCH_ERRORS as e:
                print(f"  warning: skipping r/{sub}: {e}", file=sys.stderr)
        topic_post_count = len(posts)
        topics_result = topics.analyze_anime_topics(posts)

    ip_counts, candidates, ip_trend = Counter(), Counter(), []
    ip_post_count = 0
    if not skip_ip:
        ip_posts = []
        for sub in config.IP_TRACKING_SUBREDDITS:
            print(f"Fetching r/{sub}...", file=sys.stderr)
            try:
                ip_posts.extend(client.fetch_listing(
                    sub, sort="top", time_filter=config.TIME_FILTER,
                    limit=config.POSTS_PER_SUBREDDIT,
                ))
            except FETCH_ERRORS as e:
                print(f"  warning: skipping r/{sub}: {e}", file=sys.stderr)
        ip_post_count = len(ip_posts)

        ip_counts, _examples = ip_tracker.extract_ip_mentions(ip_posts)
        candidates = ip_tracker.extract_candidate_phrases(ip_posts)

        history = ip_tracker.HistoryStore()
        ip_trend = ip_tracker.compute_trend(ip_counts, date_str, history)
        history.save(date_str, ip_counts)

    meta = {
        "ip_subreddits": config.IP_TRACKING_SUBREDDITS,
        "trend_window_days": config.TREND_WINDOW_DAYS,
        "topic_post_count": topic_post_count,
        "ip_post_count": ip_post_count,
    }

    md = report.render_markdown(date_str, topics_result, ip_counts, ip_trend, candidates, meta)
    html = report.render_html(date_str, md)

    reports_dir = Path(config.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = reports_dir / f"{date_str}.md"
    html_path = reports_dir / f"{date_str}.html"
    md_path.write_text(md)
    html_path.write_text(html)

    print(f"Wrote {md_path} and {html_path}", file=sys.stderr)
    return md_path, html_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", default=None, help="Date to label this report (YYYY-MM-DD), default today (UTC)")
    parser.add_argument("--skip-topics", action="store_true", help="Skip the r/anime topics section")
    parser.add_argument("--skip-ip", action="store_true", help="Skip the AI-anime IP-tracking section")
    args = parser.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run(date_str, skip_topics=args.skip_topics, skip_ip=args.skip_ip)


if __name__ == "__main__":
    main()
