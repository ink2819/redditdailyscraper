# redditdailyscraper

Daily report generator that answers two questions:

1. **What's most discussed on r/anime right now?** (aggregated by show, using
   r/anime's episode-discussion title convention, e.g. `Frieren: Beyond
   Journey's End - Episode 12 discussion`)
2. **Which anime IPs are being shared/rising fastest in the AI-anime-art
   subreddits** (currently r/NovelAi and r/StableDiffusion)?

## How it works

Reddit exposes every listing page as JSON if you append `.json` to the URL
(e.g. `https://www.reddit.com/r/anime/top.json?t=day`) - no login or API key
needed. This script uses `requests` against those endpoints instead of
scraping rendered HTML with bs4, because Reddit's HTML is JS-rendered and
changes shape often; the JSON endpoints are stable and structured. `bs4` is
still used, just for the one place raw HTML actually shows up: cleaning a
self-post's `selftext_html`.

- `reddit_scraper/client.py` - throttled JSON client with retries/backoff
- `reddit_scraper/topics.py` - groups r/anime posts into per-show discussion volume
- `reddit_scraper/ip_tracker.py` - keyword-matches known IPs, surfaces
  unlisted candidate names, and computes "fastest rising" against saved
  daily history snapshots in `data/history/`
- `reddit_scraper/report.py` - renders Markdown + a small self-contained HTML page
- `main.py` - CLI entrypoint

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py                    # today's report -> reports/<date>.md and .html
python main.py --date 2026-08-25  # backfill/relabel a specific date
python main.py --skip-ip          # r/anime topics only
python main.py --skip-topics      # AI-anime IP tracking only
```

Each run also writes a snapshot of today's IP mention counts to
`data/history/<date>.json`. "Fastest rising" is computed by comparing
today's counts against the trailing 7-day average from those snapshots, so
**the trend numbers get meaningful once you've run this daily for a few
days** - the first few runs will show "not enough data yet".

## Configuration (`reddit_scraper/config.py`)

- `TOPIC_SUBREDDITS` / `IP_TRACKING_SUBREDDITS` - which subreddits to pull from.
  r/NovelAi and r/StableDiffusion are the two large, real, active subreddits
  for AI anime art; add more just by adding names to the list (no code
  changes needed) - a subreddit that doesn't exist/is private is skipped
  with a warning rather than failing the whole run.
- `KNOWN_IPS` - the anime title/character keyword list used for IP mention
  matching, with aliases. This is a **starting list, not exhaustive** -
  extend it as you notice gaps.
- To help with that: the report's "Unlisted names worth reviewing" section
  surfaces repeated capitalized phrases (e.g. character names) that showed
  up 3+ times but aren't in `KNOWN_IPS` yet, so you can promote real IPs
  into the config over time instead of silently missing them.

## Testing

```bash
python -m pytest
```

Tests run entirely offline against fixture data (no network calls), covering
the r/anime grouping logic, IP keyword matching, trend math, report
rendering, and the JSON-client's pagination/retry/error handling.

## Scheduling

Not wired up yet by design - run it manually first and sanity-check a few
days of reports. Once you're happy with it, the natural next step is a daily
cron job or a GitHub Actions workflow (`schedule: cron`) that runs
`python main.py` and commits/publishes the generated report.

## Known limitations

- Reddit's unauthenticated JSON endpoints have a fairly strict per-IP rate
  limit; the client throttles to ~1 request/1.5s and retries on 429, but if
  you run this very frequently you may still get rate-limited. For heavier
  use, switch to [PRAW](https://praw.readthedocs.io/) with a registered
  Reddit app (OAuth) instead.
- "Most discussed" for r/anime relies on the episode-discussion title
  convention; non-episode posts (news, fanart, megathreads) are ranked
  separately by comment count rather than being folded into a show.
- IP detection is keyword-based, not real NLP - it will miss anything not in
  `KNOWN_IPS` and its aliases (mitigated by the candidate-surfacing section
  above, but still not exhaustive).
