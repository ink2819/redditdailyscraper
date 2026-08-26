import pytest

from reddit_scraper import client as client_module
from reddit_scraper.client import RedditClient, SubredditUnavailable


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def _listing_payload(titles, after=None):
    return {
        "data": {
            "children": [{"data": {"title": t, "num_comments": 0, "score": 0}} for t in titles],
            "after": after,
        }
    }


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(client_module.time, "sleep", lambda *_: None)


def test_fetch_listing_paginates_until_no_after(monkeypatch):
    pages = [
        _listing_payload(["a", "b"], after="t3_page2"),
        _listing_payload(["c"], after=None),
    ]
    calls = []

    def fake_get(url, params=None, timeout=15):
        calls.append(params)
        return FakeResponse(200, pages.pop(0))

    c = RedditClient()
    monkeypatch.setattr(c.session, "get", fake_get)

    posts = c.fetch_listing("anime", sort="top", time_filter="day", limit=200)

    assert [p["title"] for p in posts] == ["a", "b", "c"]
    assert "after" not in calls[0]
    assert calls[1]["after"] == "t3_page2"


def test_fetch_listing_raises_on_404(monkeypatch):
    def fake_get(url, params=None, timeout=15):
        return FakeResponse(404, text="not found")

    c = RedditClient()
    monkeypatch.setattr(c.session, "get", fake_get)

    with pytest.raises(SubredditUnavailable):
        c.fetch_listing("doesnotexist12345")


def test_fetch_listing_retries_on_429_then_succeeds(monkeypatch):
    responses = [FakeResponse(429, text="slow down"), FakeResponse(200, _listing_payload(["ok"]))]

    def fake_get(url, params=None, timeout=15):
        return responses.pop(0)

    c = RedditClient()
    monkeypatch.setattr(c.session, "get", fake_get)

    posts = c.fetch_listing("anime", limit=100)
    assert [p["title"] for p in posts] == ["ok"]
