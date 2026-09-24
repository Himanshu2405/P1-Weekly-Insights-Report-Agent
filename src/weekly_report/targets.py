"""The 2026 plan: weekly targets = same week last year x (1 + planned growth).

Generated ONCE and frozen in a versioned CSV (like a plan Finance hands over at the start of the year).
The pipeline only reads the file; it never recomputes targets from live data.
"""

from datetime import datetime, timedelta, timezone

import pandas as pd

from . import config
from .bq import BigQueryRunner
from .weeks import fiscal_year_weeks, same_week_last_year


def generate(runner: BigQueryRunner) -> pd.DataFrame:
    weeks = fiscal_year_weeks(config.PLAN_YEAR)
    ly_weeks = [same_week_last_year(w) for w in weeks]
    last_ly_week_end = datetime.combine(ly_weeks[-1] + timedelta(days=7), datetime.min.time(), timezone.utc) - timedelta(microseconds=1)
    facts = runner.run("weekly_facts", start_week=ly_weeks[0], data_through=last_ly_week_end)
    facts["week_start"] = pd.to_datetime(facts["week_start"]).dt.date
    by_week = facts.groupby("week_start")[["orders", "revenue"]].sum()

    growth = 1 + config.PLAN_GROWTH_PCT / 100
    rows = []
    for w, ly in zip(weeks, ly_weeks):
        if ly not in by_week.index:
            raise ValueError(f"No actuals for last-year week {ly}; cannot build target for {w}")
        ly_orders = int(by_week.at[ly, "orders"])
        ly_revenue = float(by_week.at[ly, "revenue"])
        rows.append({
            "week_start": w.isoformat(),
            "orders_target": round(ly_orders * growth),
            "revenue_target": round(ly_revenue * growth),
            "ly_week_start": ly.isoformat(),
            "ly_orders": ly_orders,
            "ly_revenue": round(ly_revenue),
            "plan_growth_pct": config.PLAN_GROWTH_PCT,
            "target_version": config.TARGET_VERSION,
        })
    return pd.DataFrame(rows)


def load() -> pd.DataFrame:
    df = pd.read_csv(config.TARGETS_FILE, parse_dates=["week_start"])
    df["week_start"] = df["week_start"].dt.date
    return df.set_index("week_start")
