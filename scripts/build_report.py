"""Full data-side run: query BigQuery once, save the data brief, render the HTML report.

Usage:
    python scripts/build_report.py                    # latest completed week
    python scripts/build_report.py --week 2026-06-15  # a specific past week
"""

import argparse
import sys
from datetime import date, datetime, timezone

from weekly_report.pipeline import collect, save_brief
from weekly_report.render import render
from weekly_report.weeks import latest_completed_week, week_start


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week", type=date.fromisoformat, help="Monday of the week to report (default: latest completed)")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    reporting = week_start(args.week) if args.week else latest_completed_week(now)
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
