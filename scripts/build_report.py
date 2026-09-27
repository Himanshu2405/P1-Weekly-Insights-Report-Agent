"""Full run for a week: query BigQuery, save the brief, AI commentary (guards, retry, fallback), log, render.

Usage:
    python scripts/build_report.py                    # config.AS_OF_WEEK (or latest completed week if None)
    python scripts/build_report.py --week 2026-06-15  # a specific past week
    python scripts/build_report.py --backfill         # also build the archive weeks before it
    python scripts/build_report.py --no-ai            # numbers and charts only
    python scripts/build_report.py --no-cache         # force a fresh Claude call even if the brief is unchanged
"""

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

from weekly_report import config

from weekly_report.commentary import log_run, produce
from weekly_report.pipeline import collect, save_brief
from weekly_report.render import render
from weekly_report.weeks import latest_completed_week, week_start


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week", type=date.fromisoformat, help="Monday of the week to report (default: config.AS_OF_WEEK)")
    parser.add_argument("--backfill", action="store_true", help=f"also build the {config.ARCHIVE_WEEKS} previous weeks")
    parser.add_argument("--no-ai", action="store_true", help="skip the AI commentary")
    parser.add_argument("--no-cache", action="store_true", help="always call Claude, even for an unchanged brief")
    parser.add_argument("--version", default=config.PROMPT_VERSION, help="prompt version, e.g. v1")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    reporting = week_start(args.week) if args.week else (config.AS_OF_WEEK or latest_completed_week(now))
    weeks = [reporting - timedelta(weeks=i) for i in range(config.ARCHIVE_WEEKS, 0, -1)] if args.backfill else []
    status = 0
    for w in weeks + [reporting]:  # oldest first, so the as-of week is rendered last and becomes index.html
        status = max(status, build(w, now, ai=not args.no_ai, use_cache=not args.no_cache, version=args.version))
    return status


def build(reporting: date, now: datetime, ai: bool = True, use_cache: bool = True, version: str = config.PROMPT_VERSION) -> int:
    run = collect(reporting, now)
    brief_name = save_brief(run)
    if not run.brief.data_quality.all_passed:
        failed = [c.name for c in run.brief.data_quality.checks if not c.passed]
        print(f"Data-quality gate FAILED for week {reporting}: {failed}. Report not rendered.")
        return 2
    outcome = None
    if ai:
        outcome = produce(run.brief, version=version, use_cache=use_cache)
        log_run(run.brief, outcome, run.bytes_billed)
        blocks = [c for c in (outcome.guard_report or {}).get("checks", []) if c["severity"] == "block"]
        warns = [c["name"] for c in (outcome.guard_report or {}).get("checks", []) if c["severity"] == "warn" and not c["passed"]]
        print(f"  AI commentary: {outcome.status.upper()}"
              f"{' (cached, no new call)' if outcome.cache_hit else ''} | attempts {len(outcome.attempts)} | "
              f"blocking checks {sum(c['passed'] for c in blocks)}/{len(blocks)} | warnings {len(warns)} | "
              f"${outcome.cost_usd:.4f} | {outcome.duration_ms / 1000:.1f} s")
        for w_ in warns:
            print(f"    warning: {w_}")
        for a in outcome.attempts:
            if a.blocking_failures or a.error:
                print(f"    attempt {a.number}: {a.error or 'failed ' + ', '.join(a.blocking_failures)}")
    out = render(run, outcome)
    print(f"Week {reporting}: brief -> briefs/{brief_name}, report -> {out.relative_to(out.parents[2])} "
          f"({run.bytes_billed / 1e6:.0f} MB billed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
