"""Consolidate sharded scan results into ONE Telegram digest.

The product-companies scan is split into parallel shards; each shard writes its
scored jobs to a `last_scan.json` it uploads as an artifact. This runs in the
consolidation job (with `if: always()`) and sends a single message:

  - matches found        -> one digest of the top-N across all shards, flagged
                            "PARTIAL" if fewer shards completed than expected
  - shards ran, no match -> a short "no matches" note
  - zero shards produced -> a hard failure alert

So a timeout that kills some shards still delivers the shards that finished (no
wasted spend), and a total wipeout still reports instead of going silent.
"""
import argparse
import glob
import json
import os
from datetime import datetime
from pathlib import Path

from job_hunt.notifier import send_telegram
from job_hunt.scanner import format_telegram_message


def load_results(paths: list[str]) -> list[dict]:
    """Read every shard's last_scan.json (a list of scored-job dicts) and merge."""
    jobs: list[dict] = []
    for p in paths:
        try:
            data = json.loads(Path(p).read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            jobs.extend(x for x in data if isinstance(x, dict))
    return jobs


def dedup_top(jobs: list[dict], min_score: int, top_n: int) -> list[dict]:
    """Filter to score>=min_score, dedup by url, sort desc, cap at top_n."""
    seen: set = set()
    out: list[dict] = []
    for j in sorted(jobs, key=lambda x: x.get("score") or 0, reverse=True):
        if (j.get("score") or 0) < min_score:
            continue
        u = j.get("url")
        if u in seen:
            continue
        seen.add(u)
        out.append(j)
    return out[:top_n]


def build_message(jobs: list[dict], batches_done: int, batches_total: int,
                  min_score: int, top_n: int) -> str:
    """Build the single consolidated message for the three outcomes."""
    date_str = datetime.now().strftime("%d %b %Y")
    if batches_done == 0:
        return (f"❌ <b>Product-companies scan FAILED — {date_str}</b>\n"
                f"All {batches_total} batches errored or timed out before scanning "
                f"anything. No results.")
    top = dedup_top(jobs, min_score, top_n)
    partial = batches_done < batches_total
    status = f"{batches_done}/{batches_total} batches" + (" (PARTIAL — some timed out)" if partial else "")
    if not top:
        return (f"<b>Product-companies — {date_str}</b>\n"
                f"Scanned {status}. No matches at or above score {min_score}.")
    header = ""
    if partial:
        header = f"⚠️ <b>PARTIAL run — {status} completed before timeout</b>\n\n"
    return header + format_telegram_message(top, date_str)


def main(argv: "list[str] | None" = None) -> None:
    ap = argparse.ArgumentParser(description="Send one consolidated Telegram digest from shard results")
    ap.add_argument("--results-glob", required=True, help="glob for shard last_scan.json files")
    ap.add_argument("--batches-done", type=int, required=True, help="shards that produced results")
    ap.add_argument("--batches-total", type=int, required=True, help="shards expected")
    ap.add_argument("--config", default="config.json", help="config for min_score/top_n/telegram")
    args = ap.parse_args(argv)

    cfg = json.loads(Path(args.config).read_text()) if Path(args.config).is_file() else {}
    cand = cfg.get("candidate", {})
    min_score = int(cand.get("min_score", 60))
    top_n = int(cand.get("top_n", 20))
    tg = cfg.get("telegram", {})
    token = os.getenv("TELEGRAM_TOKEN") or tg.get("token")
    chat = os.getenv("TELEGRAM_CHAT_ID") or tg.get("chat_id")

    paths = glob.glob(args.results_glob, recursive=True)
    jobs = load_results(paths)
    msg = build_message(jobs, args.batches_done, args.batches_total, min_score, top_n)

    print(f"send_digest: {len(paths)} shard file(s), {len(jobs)} jobs merged, "
          f"batches {args.batches_done}/{args.batches_total}")
    if token and chat and not str(token).startswith("YOUR_"):
        send_telegram(token, chat, msg)
    else:
        print("send_digest: telegram not configured; message follows:\n" + msg)


if __name__ == "__main__":
    main()
