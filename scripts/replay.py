"""Held-out production replay: run held-out weeks one at a time, exactly like a live Monday run.

For each week: BigQuery -> brief -> AI commentary (production prompt, guards, retry, fallback) -> run log
-> rendered page, then the LLM judge scores the 4 quality rules (these weeks have no answer keys; they were
never used for tuning). Stops after a week with a problem so it can be reviewed before the next week.

Usage:
    python scripts/replay.py                        # Jul 6 to Aug 3, stop on the first problem
    python scripts/replay.py --from 2026-07-20      # resume from a week
    python scripts/replay.py --no-stop              # run all weeks regardless
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from weekly_report import config
from weekly_report.commentary import log_run, produce
from weekly_report.judge import judge
from weekly_report.pipeline import collect, save_brief
from weekly_report.render import render

REPLAY_WEEKS = [date(2026, 7, 6) + timedelta(weeks=i) for i in range(5)]  # Jul 6 .. Aug 3
OUT = config.ROOT / "evals" / "replay"
MIN_SO_WHAT_SHARE = 0.80


def run_week(week: date, now: datetime) -> dict:
    run = collect(week, now)
    save_brief(run)
    if not run.brief.data_quality.all_passed:
        return {"week": week.isoformat(), "status": "data_quality_failed", "problems": ["data-quality gate failed"]}
    outcome = produce(run.brief)
    log_run(run.brief, outcome, run.bytes_billed)
    render(run, outcome)
    row = {"week": week.isoformat(), "status": outcome.status, "attempts": len(outcome.attempts),
           "prompt_version": outcome.prompt_version, "cost_usd": outcome.cost_usd,
           "warnings": [c["name"] for c in (outcome.guard_report or {}).get("checks", [])
                        if c["severity"] == "warn" and not c["passed"]],
           "rejected_attempts": [{"attempt": a.number, "failures": a.guard_details or a.error} for a in outcome.attempts if not a.ok],
           "problems": []}
    if outcome.status == "fallback":
        row["problems"].append("fallback: commentary not published")
        return row
    key = {"week": week.isoformat(), "scenario": "held-out replay week (no answer key)", "must_say": [], "must_not_say": []}
    verdicts, so_whats, res = judge(key, outcome.commentary, brief=run.brief)
    share = sum(w["verdict"] == "implication" for w in so_whats) / len(so_whats)
    row.update(judge_cost_usd=res.cost_usd, so_what_share=round(share, 3),
               quality_fails=[v["id"] for v in verdicts if v["verdict"] == "fail"], verdicts=verdicts, so_whats=so_whats)
    if row["quality_fails"]:
        row["problems"].append(f"quality rules failed: {', '.join(row['quality_fails'])}")
    if share < MIN_SO_WHAT_SHARE:
        row["problems"].append(f"so-what share {share:.0%} below {MIN_SO_WHAT_SHARE:.0%}")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="start", type=date.fromisoformat, default=REPLAY_WEEKS[0])
    parser.add_argument("--no-stop", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    for week in [w for w in REPLAY_WEEKS if w >= args.start]:
        row = run_week(week, now)
        (OUT / f"replay_{week.isoformat()}.json").write_text(json.dumps(row, indent=2))
        print(f"{row['week']}  {row['status']:21} attempts {row.get('attempts', '-')}  "
              f"so-whats {row.get('so_what_share', '-')}  quality fails {row.get('quality_fails', '-')}  "
              f"${row.get('cost_usd', 0) + row.get('judge_cost_usd', 0):.3f}  problems: {row['problems'] or 'none'}", flush=True)
        if row["problems"] and not args.no_stop:
            print(f"Stopped after {week}: review before continuing (python scripts/replay.py --from {week + timedelta(weeks=1)}).")
            return 3
    summarize()
    return 0


def summarize() -> None:
    rows = [json.loads(p.read_text()) for p in sorted(OUT.glob("replay_*.json"))]
    lines = ["# Held-out production replay (prompt in production, Jul 6 to Aug 3)", "",
             "| Week | Status | Attempts | So-whats real implications | Quality fails | Warnings | Cost (report + judge) |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['week']} | {r['status']} | {r.get('attempts', '-')} | "
                     f"{format(r['so_what_share'], '.0%') if 'so_what_share' in r else '-'} | "
                     f"{', '.join(r.get('quality_fails', [])) or '-'} | {len(r.get('warnings', []))} | "
                     f"${r.get('cost_usd', 0) + r.get('judge_cost_usd', 0):.3f} |")
    (OUT / "replay_summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
