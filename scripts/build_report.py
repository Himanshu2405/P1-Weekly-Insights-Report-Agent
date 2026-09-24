"""Full data-side run: query BigQuery once, save the data brief, render the HTML report.

Usage:
    python scripts/build_report.py                    # config.AS_OF_WEEK (or latest completed week if None)
    python scripts/build_report.py --week 2026-06-15  # a specific past week
    python scripts/build_report.py --backfill         # also build the archive weeks before it
"""

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

from weekly_report import config

from weekly_report.pipeline import collect, save_brief
from weekly_report.render import render
from weekly_report.weeks import latest_completed_week, week_start


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week", type=date.fromisoformat, help="Monday of the week to report (default: config.AS_OF_WEEK)")
    parser.add_argument("--backfill", action="store_true", help=f"also build the {config.ARCHIVE_WEEKS} previous weeks")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    reporting = week_start(args.week) if args.week else (config.AS_OF_WEEK or latest_completed_week(now))
    weeks = [reporting - timedelta(weeks=i) for i in range(config.ARCHIVE_WEEKS, 0, -1)] if args.backfill else []
    status = 0
    for w in weeks + [reporting]:  # oldest first, so the as-of week is rendered last and becomes index.html
        status = max(status, build(w, now))
    return status


def build(reporting: date, now: datetime) -> int:
    run = collect(reporting, now)
    brief_name = save_brief(run)
    if not run.brief.data_quality.all_passed:
        failed = [c.name for c in run.brief.data_quality.checks if not c.passed]
        print(f"Data-quality gate FAILED for week {reporting}: {failed}. Report not rendered.")
        return 2
    out = render(run)
    print(f"Week {reporting}: brief -> briefs/{brief_name}, report -> {out.relative_to(out.parents[2])} "
          f"({run.bytes_billed / 1e6:.0f} MB billed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
