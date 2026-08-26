"""PRAW-based client for Reddit's official OAuth API.

We started with plain `requests` against Reddit's anonymous `.json` endpoints
(no login needed) - that works fine from a residential/local IP, but Reddit's
anti-bot filtering hard-blocks anonymous JSON scraping from cloud/CI IP
ranges (GitHub Actions included) with an instant 403, regardless of headers
or backoff. The fix isn't "retry harder" - it's to authenticate: PRAW talks
to oauth.reddit.com using a registered Reddit app's client_id/client_secret
(no username/password required for read-only access to public data), which
isn't subject to that anonymous-traffic block. See README.md for how to
register the app and where to put the credentials.

bs4 is used only for the one place raw HTML actually shows up: cleaning a
self-post's rendered body (`selftext_html`).
"""

import os

import praw
import prawcore
from bs4 import BeautifulSoup

from . import config


class SubredditUnavailable(Exception):
    """Raised when a subreddit is missing, private, banned, or quarantined."""


class MissingCredentials(Exception):
    """Raised when REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET aren't set."""


class RedditClient:
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        client_id = client_id or os.environ.get("REDDIT_CLIENT_ID")
        client_secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise MissingCredentials(
                "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are not set. "
                "Register a 'script' app at https://www.reddit.com/prefs/apps "
                "and set them as env vars (or GitHub Actions secrets) - see README.md."
            )

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent or os.environ.get("REDDIT_USER_AGENT") or config.USER_AGENT,
        )
        self.reddit.read_only = True

    def fetch_listing(self, subreddit, sort="top", time_filter=None, limit=200):
        """Fetch up to `limit` posts from a subreddit listing."""
        sub = self.reddit.subreddit(subreddit)
        try:
            if sort == "hot":
                generator = sub.hot(limit=limit)
            else:
                generator = sub.top(time_filter=time_filter or "day", limit=limit)

            posts = [
                {
                    "title": s.title,
                    "num_comments": s.num_comments,
                    "score": s.score,
                    "permalink": s.permalink,
                    "url": s.url,
                    "link_flair_text": s.link_flair_text,
                    "selftext_html": getattr(s, "selftext_html", None),
                }
                for s in generator
            ]
        except (prawcore.exceptions.Forbidden, prawcore.exceptions.NotFound,
                prawcore.exceptions.Redirect) as e:
            raise SubredditUnavailable(
                f"r/{subreddit} is private, banned, quarantined, or doesn't exist: {e}"
            ) from e

        return posts

    def subreddit_exists(self, subreddit):
        try:
            self.reddit.subreddit(subreddit).id
        except (prawcore.exceptions.Forbidden, prawcore.exceptions.NotFound,
                prawcore.exceptions.Redirect):
            return False
        return True


def clean_selftext_html(selftext_html):
    """Strip Reddit's HTML-encoded selftext_html down to plain text via bs4."""
    if not selftext_html:
        return ""
    soup = BeautifulSoup(selftext_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)
