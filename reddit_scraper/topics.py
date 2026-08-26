"""'Most discussed topics' analysis for r/anime.

r/anime's episode-discussion threads follow a consistent title convention:
    "<Show Name> - Episode 12 discussion"
    "<Show Name> - Episode 12 discussion [SPOILERS]"
So aggregating by the extracted show name (summing comments across every
episode thread for that show) gives a real per-show discussion-volume ranking,
which is a much better "most discussed" signal than any single post's score.

Posts that don't match the pattern (news, megathreads, fan art, etc.) are kept
as their own standalone entries ranked by comment count.
"""

import re
from collections import defaultdict

EPISODE_TITLE_RE = re.compile(
    r"^(?P<show>.+?)\s*-\s*Episode\s+\d+.*?discussion",
    re.IGNORECASE,
)


def _post_url(post):
    permalink = post.get("permalink", "")
    return f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")


def analyze_anime_topics(posts, top_n=15):
    """Returns {'shows': [...], 'standalone': [...]} sorted by discussion volume."""
    show_groups = defaultdict(lambda: {"thread_count": 0, "total_comments": 0,
                                        "total_score": 0, "sample_url": None})
    standalone = []

    for post in posts:
        title = post.get("title", "")
        comments = post.get("num_comments", 0) or 0
        score = post.get("score", 0) or 0
        match = EPISODE_TITLE_RE.match(title)

        if match:
            show = match.group("show").strip()
            group = show_groups[show]
            group["thread_count"] += 1
            group["total_comments"] += comments
            group["total_score"] += score
            if group["sample_url"] is None:
                group["sample_url"] = _post_url(post)
        else:
            standalone.append({
                "title": title,
                "comments": comments,
                "score": score,
                "url": _post_url(post),
            })

    shows = [
        {"show": show, **stats}
        for show, stats in show_groups.items()
    ]
    shows.sort(key=lambda s: s["total_comments"], reverse=True)
    standalone.sort(key=lambda s: s["comments"], reverse=True)

    return {
        "shows": shows[:top_n],
        "standalone": standalone[:top_n],
    }
