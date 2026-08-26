import json

from reddit_scraper import ip_tracker

KNOWN_IPS = {
    "Frieren": ["Sousou no Frieren"],
    "Chainsaw Man": ["CSM"],
}


def make_post(title, flair=None):
    return {"title": title, "link_flair_text": flair}


def test_extract_ip_mentions_matches_canonical_and_alias():
    posts = [
        make_post("My Frieren LoRA test run"),
        make_post("Sousou no Frieren fanart, feedback wanted"),
        make_post("CSM Power fan art"),
        make_post("Totally unrelated post about cats"),
    ]
    counts, examples = ip_tracker.extract_ip_mentions(posts, KNOWN_IPS)

    assert counts["Frieren"] == 2
    assert counts["Chainsaw Man"] == 1
    assert examples["Chainsaw Man"] == "CSM Power fan art"


def test_extract_ip_mentions_uses_word_boundaries():
    # "CSM" as a substring of another word shouldn't match
    posts = [make_post("MUSCSMASHUP render, unrelated to any known IP")]
    counts, _ = ip_tracker.extract_ip_mentions(posts, KNOWN_IPS)
    assert counts["Chainsaw Man"] == 0


def test_extract_candidate_phrases_ignores_known_ips_and_needs_min_mentions():
    posts = (
        [make_post("Frieren LoRA test")] * 5  # known IP, should be excluded
        + [make_post("Marin Kitagawa cosplay render")] * 3
        + [make_post("Marin Kitagawa cosplay render")]  # 4th mention total
        + [make_post("Onetime Name here")]  # only 1 mention, below threshold
    )
    candidates = ip_tracker.extract_candidate_phrases(posts, KNOWN_IPS)
    assert "Frieren" not in candidates
    assert candidates["Marin Kitagawa"] == 4
    assert "Onetime Name" not in candidates


def test_history_store_round_trip(tmp_path):
    store = ip_tracker.HistoryStore(history_dir=tmp_path)
    store.save("2026-08-20", {"Frieren": 10})
    loaded = store.load("2026-08-20")
    assert loaded == {"Frieren": 10}
    assert store.load("2026-08-19") is None


def test_compute_trend_flags_rising_ip(tmp_path):
    store = ip_tracker.HistoryStore(history_dir=tmp_path)
    for d, count in [("2026-08-18", 2), ("2026-08-19", 2), ("2026-08-20", 2)]:
        store.save(d, {"Frieren": count})

    today_counts = {"Frieren": 20, "Chainsaw Man": 5}
    trend = ip_tracker.compute_trend(today_counts, "2026-08-21", store, window_days=7)

    by_ip = {r["ip"]: r for r in trend}
    assert by_ip["Frieren"]["baseline_avg"] == 2.0
    assert by_ip["Frieren"]["delta"] == 18.0
    # brand-new IP with no history should still show up, ranked below the huge riser
    assert by_ip["Chainsaw Man"]["baseline_avg"] == 0.0
    assert trend[0]["ip"] == "Frieren"


def test_compute_trend_with_no_history_treats_baseline_as_zero(tmp_path):
    store = ip_tracker.HistoryStore(history_dir=tmp_path)
    trend = ip_tracker.compute_trend({"Frieren": 5}, "2026-08-21", store)
    assert trend[0]["baseline_avg"] == 0.0
    assert trend[0]["delta"] == 5.0
