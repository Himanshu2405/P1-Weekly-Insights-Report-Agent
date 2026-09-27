"""Batch runner: generate commentary for every golden week with one prompt version, exactly like production.

Each run is an "experiment" folder under evals/experiments/ holding one commentary file per week
(including rejected attempts), plus summary.json and summary.md. Re-running the same experiment name
skips weeks that are already done, so an interrupted run can be resumed.

Usage:
    python scripts/run_golden.py                          # prompt v1, Opus 5, all 16 weeks
    python scripts/run_golden.py --version v2 --name v2_opus5
    python scripts/run_golden.py --weeks 2026-02-16 2026-03-30
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from weekly_report import config
from weekly_report.commentary import produce
from weekly_report.models import DataBrief

SETS = {"golden": config.ROOT / "evals" / "golden" / "briefs", "heldout": config.ROOT / "evals" / "heldout" / "briefs"}
EXPERIMENTS = config.ROOT / "evals" / "experiments"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default=config.PROMPT_VERSION)
    parser.add_argument("--model", default=config.LLM_MODEL)
    parser.add_argument("--name", help="experiment name (default: <version>_<model>)")
    parser.add_argument("--weeks", nargs="*", help="subset of weeks (YYYY-MM-DD)")
    parser.add_argument("--set", choices=list(SETS), default="golden", help="golden (answer keys) or heldout (never tuned on)")
    args = parser.parse_args()

    name = args.name or ("" if args.set == "golden" else "heldout_") + f"{args.version}_{args.model.replace('claude-', '')}"
    out = EXPERIMENTS / name
    out.mkdir(parents=True, exist_ok=True)
    briefs = sorted(SETS[args.set].glob("brief_*.json"))
    if args.weeks:
        briefs = [b for b in briefs if b.stem.removeprefix("brief_") in args.weeks]

    print(f"Experiment {name}: prompt {args.version}, {args.model}, {len(briefs)} weeks -> {out.relative_to(config.ROOT)}")
    rows, started = [], time.monotonic()
    for i, path in enumerate(briefs, 1):
        brief = DataBrief.model_validate_json(path.read_text())
        week = brief.meta.reporting_week.start.isoformat()
        o = produce(brief, version=args.version, model=args.model, out_dir=out)  # resumes via the per-week file
        checks = (o.guard_report or {}).get("checks", [])
        row = {
            "week": week, "status": o.status, "reused": o.cache_hit, "attempts": len(o.attempts),
            "first_attempt_passed": bool(o.attempts and o.attempts[0].ok),
            "blocking_failures": sorted({f for a in o.attempts for f in a.blocking_failures}),
            "errors": [a.error for a in o.attempts if a.error],
            "warnings": [c["name"] for c in checks if c["severity"] == "warn" and not c["passed"]],
            "cost_usd": o.cost_usd, "duration_s": round(o.duration_ms / 1000, 1),
        }
        rows.append(row)
        print(f"  [{i:2}/{len(briefs)}] {week}  {o.status:21} attempts {row['attempts']}  "
              f"warnings {len(row['warnings'])}  ${o.cost_usd:.3f}  {row['duration_s']:5.1f} s"
              f"{'  (already done)' if o.cache_hit else ''}", flush=True)

    n = len(rows)
    summary = {
        "experiment": name, "set": args.set, "prompt_version": args.version, "model": args.model,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "weeks": n,
        "verified_first_attempt": sum(r["first_attempt_passed"] for r in rows),
        "verified_after_retry": sum(r["status"] == "verified_after_retry" for r in rows),
        "fallback": sum(r["status"] == "fallback" for r in rows),
        "weeks_with_warnings": sum(bool(r["warnings"]) for r in rows),
        "total_cost_usd": round(sum(r["cost_usd"] for r in rows), 3),
        "avg_cost_per_week_usd": round(sum(r["cost_usd"] for r in rows) / n, 3) if n else 0,
        "avg_duration_s": round(sum(r["duration_s"] for r in rows) / n, 1) if n else 0,
        "wall_clock_min": round((time.monotonic() - started) / 60, 1),
        "rows": rows,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    (out / "summary.md").write_text(to_markdown(summary))
    print(f"\nFirst-attempt pass {summary['verified_first_attempt']}/{n} | after retry {summary['verified_after_retry']} | "
          f"fallback {summary['fallback']} | warnings in {summary['weeks_with_warnings']} weeks | "
          f"${summary['total_cost_usd']} total, ${summary['avg_cost_per_week_usd']}/week")
    return 0


def to_markdown(s: dict) -> str:
    lines = [f"# Experiment {s['experiment']}", "",
             f"Prompt {s['prompt_version']}, model {s['model']}, {s['weeks']} {s.get('set', 'golden')} weeks, finished {s['finished_at_utc']}.", "",
             "| Metric | Value |", "|---|---|",
             f"| Passed guards on first attempt | {s['verified_first_attempt']} of {s['weeks']} |",
             f"| Passed after one retry | {s['verified_after_retry']} |",
             f"| Fallback (not published) | {s['fallback']} |",
             f"| Weeks with warnings | {s['weeks_with_warnings']} |",
             f"| Total cost (API equivalent) | ${s['total_cost_usd']} |",
             f"| Average cost per week | ${s['avg_cost_per_week_usd']} |",
             f"| Average time per week | {s['avg_duration_s']} s |", "",
             "| Week | Status | Attempts | Blocking failures | Warnings | Cost | Time |", "|---|---|---|---|---|---|---|"]
    for r in s["rows"]:
        lines.append(f"| {r['week']} | {r['status']} | {r['attempts']} | {', '.join(r['blocking_failures']) or '-'} | "
                     f"{', '.join(r['warnings']) or '-'} | ${r['cost_usd']:.3f} | {r['duration_s']} s |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
