"""Build and save the data brief for the latest completed week (or a given week for backfills).

Usage:
    python scripts/build_brief.py                    # latest completed week
    python scripts/build_brief.py --week 2026-06-15  # a specific past week (golden-set backfill)
"""

import argparse
import sys
from datetime import date, datetime, timedelta, timezone

from weekly_report import config, targets
from weekly_report.bq import BigQueryRunner
from weekly_report.brief import assemble, split_facts
from weekly_report.weeks import latest_completed_week, report_weeks, week_start


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week", type=date.fromisoformat, help="Monday of the week to report (default: latest completed)")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    reporting = week_start(args.week) if args.week else latest_completed_week(now)
    weeks = report_weeks(reporting)

    runner = BigQueryRunner()
    facts = runner.run("weekly_facts", start_week=reporting - timedelta(weeks=config.LOOKBACK_WEEKS),
                       data_through=weeks.data_through)
    weekly, cuts = split_facts(facts, weeks)
    brief = assemble(weekly, cuts, targets.load(), weeks, now=now)

    config.BRIEFS_DIR.mkdir(exist_ok=True)
    out = config.BRIEFS_DIR / f"brief_{reporting.isoformat()}.json"
    out.write_text(brief.model_dump_json(indent=2))

    k, t = brief.kpis, brief.targets
    print(f"Brief for week {reporting} -> {out.name} ({runner.bytes_billed / 1e6:.0f} MB billed)")
    print(f"  data quality: {'PASS' if brief.data_quality.all_passed else 'FAIL'}")
    for c in brief.data_quality.checks:
        print(f"    [{'x' if c.passed else ' '}] {c.name}: {c.detail}")
    print(f"  orders {k.orders.value:,.0f} ({k.orders.wow_change:+.1f}% WoW, {k.orders.yoy_change:+.1f}% YoY), "
          f"{t.orders_vs_target.attainment_pct}% of target")
    print(f"  revenue ${k.revenue.value:,.0f} ({k.revenue.wow_change:+.1f}% WoW), {t.revenue_vs_target.attainment_pct}% of target; "
          f"QTD {t.qtd_revenue_vs_target.attainment_pct}%")
    print(f"  flags: {[f.id for f in brief.flags]}")
    return 0 if brief.data_quality.all_passed else 2


if __name__ == "__main__":
    sys.exit(main())
