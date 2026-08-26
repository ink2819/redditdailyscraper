"""Central configuration: which subreddits to scrape and the known-IP keyword list."""

# Subreddits scraped for "most discussed topics" (general r/anime discussion volume).
TOPIC_SUBREDDITS = ["anime"]

# Subreddits scraped for "AI anime circle" IP-sharing trends.
# r/NovelAi and r/StableDiffusion are the two large, active, real subreddits whose
# posts regularly reference specific anime IPs/characters (LoRAs, fan art, etc).
# Add more here as you find them (this list is just data, no code changes needed) -
# each name is checked at fetch time and skipped with a warning if it doesn't exist
# or has gone private.
IP_TRACKING_SUBREDDITS = ["NovelAi", "StableDiffusion"]

# How many posts to pull per subreddit per run (Reddit paginates in pages of ~100).
POSTS_PER_SUBREDDIT = 200

# Time window for "top" listings: hour/day/week/month/year/all
TIME_FILTER = "day"

# Known anime IPs/franchises + aliases, used for keyword matching in ip_tracker.py.
# This is intentionally a starting list, not exhaustive - extend freely.
# Format: canonical name -> list of alternate spellings/aliases to also match.
KNOWN_IPS = {
    "Frieren": ["Frieren: Beyond Journey's End", "Sousou no Frieren"],
    "Chainsaw Man": ["Chainsawman", "CSM"],
    "Jujutsu Kaisen": ["JJK"],
    "Demon Slayer": ["Kimetsu no Yaiba", "Kimetsu"],
    "My Hero Academia": ["Boku no Hero Academia", "MHA", "BNHA"],
    "One Piece": [],
    "Attack on Titan": ["Shingeki no Kyojin", "AoT", "SNK"],
    "Spy x Family": ["SpyxFamily", "SxF"],
    "Genshin Impact": ["Genshin"],
    "Honkai Star Rail": ["HSR", "Honkai: Star Rail"],
    "Fate/Grand Order": ["FGO", "Fate Grand Order"],
    "Nier Automata": ["NieR: Automata"],
    "Re:Zero": ["Re Zero", "ReZero"],
    "Konosuba": ["KonoSuba"],
    "Evangelion": ["Neon Genesis Evangelion", "NGE", "Eva"],
    "K-On": ["K-On!"],
    "Violet Evergarden": [],
    "Made in Abyss": [],
    "Fullmetal Alchemist": ["FMA", "FMAB"],
    "Naruto": ["Boruto"],
    "Bleach": [],
    "Dragon Ball": ["Dragon Ball Z", "DBZ", "Dragon Ball Super"],
    "Sword Art Online": ["SAO"],
    "Steins;Gate": ["Steins Gate"],
    "Miku": ["Hatsune Miku"],
    "Nezuko": [],
    "Zero Two": ["Darling in the Franxx"],
    "Marin Kitagawa": ["My Dress-Up Darling", "Sono Bisque Doll"],
    "Rem": [],
    "Asuka": [],
    "Mikasa": [],
    "Power": ["Chainsaw Man Power"],
    "Makima": [],
    "Bocchi the Rock": ["Bocchi"],
    "Oshi no Ko": [],
    "Blue Archive": [],
    "Nikke": ["Goddess of Victory: Nikke"],
    "Vtuber": ["VTuber", "Hololive", "Nijisanji"],
}

# Regex-based candidate detector: capitalized multi-word phrases that keep showing
# up but aren't in KNOWN_IPS yet get surfaced separately in the report so the list
# above can be grown over time instead of silently missing new/rising titles.
STOPWORDS_FOR_CANDIDATES = {
    "The", "This", "That", "What", "When", "Where", "Why", "How", "AI",
    "Stable Diffusion", "New", "First", "Best", "My", "Just", "Made",
    "Work", "Test", "WIP", "NSFW", "Discussion", "Weekly", "Daily",
    "Episode", "Season", "Chapter", "Reddit", "Post", "Image", "Model",
    "LoRA", "Prompt", "Update",
}
MIN_CANDIDATE_MENTIONS = 3

USER_AGENT = "redditdailyscraper/0.1 (daily report script; contact: set REDDIT_UA_CONTACT env var)"

HISTORY_DIR = "data/history"
REPORTS_DIR = "reports"

# How many trailing days of history to average over when computing "fastest rising".
TREND_WINDOW_DAYS = 7
