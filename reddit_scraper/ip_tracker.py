"""Tracks which anime IPs are being shared in the AI-anime-art subreddits, and
computes which ones are rising fastest by comparing today's mention count
against a trailing history of previous daily snapshots.
"""

import json
import re
from collections import Counter
from pathlib import Path

from . import config

_WORD_BOUNDARY = r"(?<![A-Za-z0-9]){}(?![A-Za-z0-9])"

# capitalized word, or capitalized word run (2-4 words), used for candidate detection
_CANDIDATE_PHRASE_RE = re.compile(
    r"\b([A-Z][a-zA-Z']+(?:\s+[A-Z][a-zA-Z']+){0,3})\b"
)


def _build_ip_patterns(known_ips):
    patterns = {}
    for canonical, aliases in known_ips.items():
        names = [canonical] + list(aliases)
        alt = "|".join(re.escape(n) for n in names)
        patterns[canonical] = re.compile(_WORD_BOUNDARY.format(f"(?:{alt})"), re.IGNORECASE)
    return patterns


def _post_text(post):
    parts = [post.get("title", ""), post.get("link_flair_text") or ""]
    return " \n ".join(parts)


def extract_ip_mentions(posts, known_ips=None):
    known_ips = known_ips or config.KNOWN_IPS
    patterns = _build_ip_patterns(known_ips)
    counts = Counter()
    examples = {}

    for post in posts:
        text = _post_text(post)
        for canonical, pattern in patterns.items():
            if pattern.search(text):
                counts[canonical] += 1
                examples.setdefault(canonical, post.get("title", ""))

    return counts, examples


def extract_candidate_phrases(posts, known_ips=None):
    """Surface repeated capitalized phrases not already in the known-IP list,
    so the config can be grown over time instead of silently missing new titles.
    """
    known_ips = known_ips or config.KNOWN_IPS
    known_patterns = _build_ip_patterns(known_ips)

    counts = Counter()
    for post in posts:
        title = post.get("title", "")
        # Mask out known-IP mentions first, so e.g. "Frieren LoRA" doesn't get
        # extracted as a whole (the greedy capitalized-run regex would otherwise
        # glue an adjacent known name onto the next capitalized word).
        masked_title = title
        for pattern in known_patterns.values():
            masked_title = pattern.sub(" ", masked_title)

        for phrase in _CANDIDATE_PHRASE_RE.findall(masked_title):
            normalized = phrase.strip()
            if normalized in config.STOPWORDS_FOR_CANDIDATES:
                continue
            if len(normalized) < 3:
                continue
            counts[normalized] += 1

    return Counter({
        phrase: n for phrase, n in counts.items()
        if n >= config.MIN_CANDIDATE_MENTIONS
    })


class HistoryStore:
    """Reads/writes daily mention-count snapshots to disk as plain JSON files,
    one per date, so 'fastest rising' can be computed against real history
    instead of being made up.
    """

    def __init__(self, history_dir=None):
        self.dir = Path(history_dir or config.HISTORY_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, date_str):
        return self.dir / f"{date_str}.json"

    def save(self, date_str, counts):
        self._path(date_str).write_text(json.dumps(dict(counts), indent=2, sort_keys=True))

    def load(self, date_str):
        path = self._path(date_str)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def trailing_days(self, before_date_str, window_days):
        """All available snapshot dates strictly before `before_date_str`,
        most recent first, up to `window_days` of them.
        """
        all_dates = sorted(p.stem for p in self.dir.glob("*.json"))
        earlier = [d for d in all_dates if d < before_date_str]
        return earlier[-window_days:]


def compute_trend(today_counts, date_str, history_store, window_days=None):
    """Returns a list of {ip, today, baseline_avg, delta, pct_change} sorted by
    delta descending (fastest rising first). `baseline_avg` is the mean count
    over the trailing window of *previously saved* days; an IP with no prior
    history is treated as baseline 0 (a brand-new mention, maximally 'rising').
    """
    window_days = window_days or config.TREND_WINDOW_DAYS
    trailing_dates = history_store.trailing_days(date_str, window_days)
    trailing_snapshots = [history_store.load(d) or {} for d in trailing_dates]

    all_ips = set(today_counts) | {ip for snap in trailing_snapshots for ip in snap}
    results = []
    for ip in all_ips:
        today_count = today_counts.get(ip, 0)
        if trailing_snapshots:
            baseline_avg = sum(snap.get(ip, 0) for snap in trailing_snapshots) / len(trailing_snapshots)
        else:
            baseline_avg = 0.0
        delta = today_count - baseline_avg
        pct_change = (delta / baseline_avg * 100) if baseline_avg > 0 else (
            100.0 if today_count > 0 else 0.0
        )
        results.append({
            "ip": ip,
            "today": today_count,
            "baseline_avg": round(baseline_avg, 2),
            "delta": round(delta, 2),
            "pct_change": round(pct_change, 1),
            "days_of_history": len(trailing_snapshots),
        })

    results.sort(key=lambda r: r["delta"], reverse=True)
    return results
