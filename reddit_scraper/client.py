"""Thin client over Reddit's public JSON endpoints (no login/API key required).

Any Reddit listing page returns structured JSON if you append ``.json`` to the
URL, e.g. https://www.reddit.com/r/anime/top.json?t=day - that's what this
client uses instead of scraping rendered HTML, which is far more stable.
bs4 is used only for the one place raw HTML actually shows up: a self-post's
rendered body (``selftext_html``), which Reddit escapes and HTML-encodes.
"""

import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from . import config

BASE_URL = "https://www.reddit.com"
REQUEST_DELAY_SECONDS = 1.5  # be polite; unauthenticated JSON endpoints rate-limit hard
MAX_RETRIES = 3


class SubredditUnavailable(Exception):
    """Raised when a subreddit is missing, private, or banned."""


class RedditClient:
    def __init__(self, user_agent=None, delay=REQUEST_DELAY_SECONDS):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent or config.USER_AGENT})
        self.delay = delay
        self._last_request_at = 0.0

    def _throttled_get(self, url, params=None):
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=15)
            except requests.exceptions.RequestException as network_err:
                last_error = f"network error: {network_err}"
                time.sleep(2 * attempt)
                continue
            self._last_request_at = time.monotonic()

            if resp.status_code == 200:
                return resp
            if resp.status_code in (403, 404):
                raise SubredditUnavailable(
                    f"{url} returned {resp.status_code} (private, banned, or nonexistent)"
                )
            if resp.status_code == 429:
                wait = 5 * attempt
                time.sleep(wait)
                last_error = f"429 rate-limited (attempt {attempt}/{MAX_RETRIES})"
                continue
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            time.sleep(2 * attempt)

        raise requests.RequestException(f"Giving up on {url}: {last_error}")

    def fetch_listing(self, subreddit, sort="top", time_filter=None, limit=200):
        """Fetch up to `limit` posts from a subreddit listing, paginating as needed."""
        posts = []
        after = None
        remaining = limit

        while remaining > 0:
            page_size = min(100, remaining)
            params = {"limit": page_size, "raw_json": 1}
            if time_filter:
                params["t"] = time_filter
            if after:
                params["after"] = after

            url = f"{BASE_URL}/r/{urllib.parse.quote(subreddit)}/{sort}.json"
            resp = self._throttled_get(url, params=params)
            payload = resp.json()

            children = payload.get("data", {}).get("children", [])
            if not children:
                break

            for child in children:
                posts.append(child.get("data", {}))

            after = payload.get("data", {}).get("after")
            remaining -= len(children)
            if not after:
                break

        return posts

    def subreddit_exists(self, subreddit):
        try:
            resp = self._throttled_get(f"{BASE_URL}/r/{urllib.parse.quote(subreddit)}/about.json")
        except SubredditUnavailable:
            return False
        data = resp.json().get("data", {})
        return bool(data.get("display_name"))


def clean_selftext_html(selftext_html):
    """Strip Reddit's HTML-encoded selftext_html down to plain text via bs4."""
    if not selftext_html:
        return ""
    soup = BeautifulSoup(selftext_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)
