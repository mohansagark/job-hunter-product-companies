"""send_digest — consolidate sharded results into one Telegram message.

Covers the three outcomes the workflow relies on: matches (with partial flag),
shards-ran-but-no-matches, and zero-batches hard failure. No network: we only
exercise the pure builders.
"""
import json

from job_hunt import send_digest


def _job(score, url, title="Engineer", company="Acme"):
    return {"score": score, "url": url, "company": company, "title": title,
            "location": "Remote", "stack": "Python", "reason": "fit"}


def test_load_and_merge_shard_files(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "last_scan.json").write_text(json.dumps([_job(90, "u1")]))
    (tmp_path / "b" / "last_scan.json").write_text(json.dumps([_job(70, "u2")]))
    jobs = send_digest.load_results([
        str(tmp_path / "a" / "last_scan.json"),
        str(tmp_path / "b" / "last_scan.json"),
    ])
    assert len(jobs) == 2


def test_dedup_top_filters_sorts_and_caps():
    jobs = [_job(50, "u1"), _job(95, "u2"), _job(80, "u2"), _job(85, "u3")]
    top = send_digest.dedup_top(jobs, min_score=60, top_n=2)
    assert [j["score"] for j in top] == [95, 85]      # sorted desc, <60 dropped
    assert len({j["url"] for j in top}) == 2           # u2 deduped, capped at 2


def test_message_with_matches_full_run():
    jobs = [_job(90, "u1"), _job(75, "u2")]
    msg = send_digest.build_message(jobs, batches_done=7, batches_total=7,
                                    min_score=60, top_n=20)
    assert "PARTIAL" not in msg
    assert "u1" in msg and "matches" in msg.lower()


def test_message_partial_run_is_flagged():
    jobs = [_job(90, "u1")]
    msg = send_digest.build_message(jobs, batches_done=4, batches_total=7,
                                    min_score=60, top_n=20)
    assert "PARTIAL" in msg and "4/7" in msg


def test_message_no_matches_but_batches_ran():
    jobs = [_job(30, "u1")]  # below threshold
    msg = send_digest.build_message(jobs, batches_done=7, batches_total=7,
                                    min_score=60, top_n=20)
    assert "No matches" in msg and "FAILED" not in msg


def test_message_zero_batches_is_hard_failure():
    msg = send_digest.build_message([], batches_done=0, batches_total=7,
                                    min_score=60, top_n=20)
    assert "FAILED" in msg and "7 batches" in msg


def test_split_for_telegram_respects_limit_and_lines():
    msg = "\n".join(f"line-{i}-{'x' * 90}" for i in range(200))  # ~18k chars
    parts = send_digest.split_for_telegram(msg, limit=4000)
    assert len(parts) > 1
    assert all(len(p) <= 4000 for p in parts)
    # No line is broken across parts; reassembly is lossless.
    assert "\n".join(parts) == msg


def test_split_for_telegram_short_message_stays_one():
    assert send_digest.split_for_telegram("short", limit=4000) == ["short"]
