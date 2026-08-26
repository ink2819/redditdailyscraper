# redditdailyscraper

Daily report generator that answers two questions:

1. **What's most discussed on r/anime right now?** (aggregated by show, using
   r/anime's episode-discussion title convention, e.g. `Frieren: Beyond
   Journey's End - Episode 12 discussion`)
2. **Which anime IPs are being shared/rising fastest in the AI-anime-art
   subreddits** (currently r/NovelAi and r/StableDiffusion)?

## How it works

Reddit exposes every listing page as JSON if you append `.json` to the URL
(e.g. `https://www.reddit.com/r/anime/top.json?t=day`) - no login needed, and
that's what this started as: `requests` straight against those endpoints.
That works fine from a home/office IP, but **Reddit's anti-bot filtering
hard-blocks anonymous JSON requests from cloud/CI IP ranges** (confirmed:
GitHub Actions' shared runners get an instant 403 on every request,
regardless of headers or backoff - this isn't rate limiting, it's an IP-based
block). So the client now goes through [PRAW](https://praw.readthedocs.io/),
which authenticates to `oauth.reddit.com` using a registered Reddit app's
`client_id`/`client_secret` (no username/password needed for read-only access
to public data) - that's the officially-supported path for automated access
and isn't subject to the anonymous-traffic block. See **Reddit API
credentials** below for one-time setup. `bs4` is still used, just for the one
place raw HTML actually shows up: cleaning a self-post's `selftext_html`.

- `reddit_scraper/client.py` - PRAW-based client (auth, fetch, error handling)
- `reddit_scraper/topics.py` - groups r/anime posts into per-show discussion volume
- `reddit_scraper/ip_tracker.py` - keyword-matches known IPs, surfaces
  unlisted candidate names, and computes "fastest rising" against saved
  daily history snapshots in `data/history/`
- `reddit_scraper/report.py` - renders Markdown + a small self-contained HTML page
- `main.py` - CLI entrypoint

## Reddit API credentials

One-time setup, free, no approval wait:

1. Go to https://www.reddit.com/prefs/apps (logged into any Reddit account)
   and click **"create app"** / **"create another app"**.
2. Name it anything, select type **"script"**, put any placeholder in the
   "redirect uri" field (e.g. `http://localhost:8080`) - it's required but
   unused for this flow.
3. After creating it, copy the string under the app name (that's your
   `client_id`) and the `secret` field (`client_secret`).

Then set:

```bash
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."
export REDDIT_USER_AGENT="redditdailyscraper/0.1 (by /u/your-username)"  # optional but recommended
```

For the GitHub Action, add the same three as **repo secrets** (Settings ->
Secrets and variables -> Actions -> New repository secret):
`REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`.

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

Tests run entirely offline against fixture data (no network calls, no
credentials needed), covering the r/anime grouping logic, IP keyword
matching, trend math, report rendering, and the client's fetch/error handling
(the PRAW layer is faked out).

## Scheduling

`.github/workflows/daily-report.yml` runs the whole pipeline (tests -> `python
main.py` -> commit `reports/` and `data/history/` back to the branch) as a
GitHub Action. It's set to **manual trigger only** for now (Actions tab ->
"Daily Reddit Report" -> "Run workflow", optionally with a `date` input) - run
it by hand a few times and sanity-check the reports before automating it.

Once you're happy with it, flip it to a daily cron by uncommenting/adding a
`schedule:` trigger in that workflow file, e.g.:

```yaml
on:
  schedule:
    - cron: "0 13 * * *"  # 13:00 UTC daily
  workflow_dispatch: {}
```

Note: `reports/` and `data/history/` are committed by the workflow (not
gitignored) specifically so the "fastest rising" trend history accumulates
across runs instead of resetting every time.

## Known limitations

- Even authenticated, Reddit's API has rate limits (PRAW handles backoff for
  you, but running this very frequently can still slow down or fail).
- "Most discussed" for r/anime relies on the episode-discussion title
  convention; non-episode posts (news, fanart, megathreads) are ranked
  separately by comment count rather than being folded into a show.
- IP detection is keyword-based, not real NLP - it will miss anything not in
  `KNOWN_IPS` and its aliases (mitigated by the candidate-surfacing section
  above, but still not exhaustive).
