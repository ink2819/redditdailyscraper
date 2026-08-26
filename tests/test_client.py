import prawcore
import pytest

from reddit_scraper.client import MissingCredentials, RedditClient, SubredditUnavailable


class FakeSubmission:
    def __init__(self, title, num_comments=0, score=0, permalink="/r/x/y/", url="",
                 link_flair_text=None, selftext_html=None):
        self.title = title
        self.num_comments = num_comments
        self.score = score
        self.permalink = permalink
        self.url = url
        self.link_flair_text = link_flair_text
        self.selftext_html = selftext_html


class FakeSubreddit:
    def __init__(self, submissions=None, error=None):
        self._submissions = submissions or []
        self._error = error

    @property
    def id(self):
        if self._error:
            raise self._error
        return "fakeid"

    def top(self, *, time_filter="all", limit=None):
        if self._error:
            raise self._error
        return iter(self._submissions[:limit] if limit else self._submissions)

    def hot(self, *, limit=None):
        if self._error:
            raise self._error
        return iter(self._submissions[:limit] if limit else self._submissions)


class FakeReddit:
    def __init__(self, subreddits):
        self._subreddits = subreddits
        self.read_only = False

    def subreddit(self, name):
        return self._subreddits[name]


def make_client(subreddits):
    c = RedditClient(client_id="test", client_secret="test", user_agent="test")
    c.reddit = FakeReddit(subreddits)
    return c


def test_missing_credentials_raises(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    with pytest.raises(MissingCredentials):
        RedditClient()


def test_fetch_listing_returns_post_dicts():
    subs = {
        "anime": FakeSubreddit([
            FakeSubmission("Frieren - Episode 1 discussion", num_comments=500, score=200),
            FakeSubmission("Weekly thread", num_comments=10, score=1),
        ])
    }
    c = make_client(subs)
    posts = c.fetch_listing("anime", sort="top", time_filter="day", limit=100)

    assert len(posts) == 2
    assert posts[0]["title"] == "Frieren - Episode 1 discussion"
    assert posts[0]["num_comments"] == 500
    assert posts[0]["score"] == 200


def test_fetch_listing_raises_subreddit_unavailable_on_forbidden():
    subs = {"private_sub": FakeSubreddit(error=prawcore.exceptions.Forbidden(
        type("R", (), {"status_code": 403})()
    ))}
    c = make_client(subs)
    with pytest.raises(SubredditUnavailable):
        c.fetch_listing("private_sub")


def test_subreddit_exists_true_and_false():
    subs = {
        "anime": FakeSubreddit([FakeSubmission("x")]),
        "doesnotexist": FakeSubreddit(error=prawcore.exceptions.NotFound(
            type("R", (), {"status_code": 404})()
        )),
    }
    c = make_client(subs)
    assert c.subreddit_exists("anime") is True
    assert c.subreddit_exists("doesnotexist") is False
