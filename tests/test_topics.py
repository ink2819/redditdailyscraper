from reddit_scraper.topics import analyze_anime_topics


def make_post(title, comments=0, score=0, permalink="/r/anime/comments/x/y/"):
    return {"title": title, "num_comments": comments, "score": score, "permalink": permalink}


def test_groups_episode_discussion_threads_by_show():
    posts = [
        make_post("Frieren: Beyond Journey's End - Episode 1 discussion", comments=500, score=200),
        make_post("Frieren: Beyond Journey's End - Episode 2 discussion [SPOILERS]", comments=700, score=300),
        make_post("Chainsaw Man - Episode 1 discussion", comments=100, score=50),
    ]
    result = analyze_anime_topics(posts)

    assert len(result["shows"]) == 2
    top = result["shows"][0]
    assert top["show"] == "Frieren: Beyond Journey's End"
    assert top["thread_count"] == 2
    assert top["total_comments"] == 1200
    assert top["total_score"] == 500
    assert top["sample_url"].startswith("https://www.reddit.com")


def test_non_episode_posts_go_to_standalone():
    posts = [
        make_post("Weekly discussion thread", comments=42, score=10),
        make_post("Fan art I made", comments=5, score=200),
    ]
    result = analyze_anime_topics(posts)

    assert result["shows"] == []
    assert len(result["standalone"]) == 2
    assert result["standalone"][0]["title"] == "Weekly discussion thread"  # ranked by comments


def test_top_n_limits_results():
    posts = [make_post(f"Show{i} - Episode 1 discussion", comments=i) for i in range(20)]
    result = analyze_anime_topics(posts, top_n=5)
    assert len(result["shows"]) == 5
    assert result["shows"][0]["show"] == "Show19"
