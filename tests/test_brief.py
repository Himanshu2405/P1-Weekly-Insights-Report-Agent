"""End-to-end brief assembly on synthetic data (no BigQuery needed)."""

from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from weekly_report import config
from weekly_report.brief import assemble, map_regions
from weekly_report.weeks import report_weeks

REPORTING = date(2026, 9, 14)
NOW = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)


def synthetic_weekly(spike: float = 1.0) -> pd.DataFrame:
    rows = []
    for i in range(70):
        w = REPORTING - timedelta(weeks=69 - i)
        orders = 1000 + i
        if w == REPORTING:
            orders = int(orders * spike)
        rows.append({"week_start": w, "orders": orders, "cancelled_orders": int(orders * 0.15),
                     "non_cancelled_orders": orders - int(orders * 0.15), "returned_14d_orders": int(orders * 0.10),
                     "revenue": (orders - int(orders * 0.15)) * 85.0, "new_signups": 500})
    return pd.DataFrame(rows)


def synthetic_cuts(countries=("China", "United States", "France", "Brasil")) -> pd.DataFrame:
    rows = []
    for w, n in ((REPORTING, 300), (REPORTING - timedelta(weeks=1), 250), (REPORTING - timedelta(days=364), 100)):
        for c in countries:
            for t in config.TRAFFIC_SOURCES:
                rows.append({"week_start": w, "country": c, "traffic_source": t, "orders": n, "revenue": n * 85.0})
    return pd.DataFrame(rows)


def synthetic_plan() -> pd.DataFrame:
    from weekly_report.weeks import fiscal_year_weeks
    weeks = fiscal_year_weeks(2026)
    return pd.DataFrame({"week_start": weeks, "orders_target": 1000, "revenue_target": 85000}).set_index("week_start")


def test_brief_validates_and_passes_quality():
    b = assemble(synthetic_weekly(), synthetic_cuts(), synthetic_plan(), report_weeks(REPORTING), now=NOW)
    assert b.data_quality.all_passed
    assert b.meta.reporting_week.week_of_quarter == 12
    ytd = b.targets.ytd_revenue_vs_target
    assert ytd.weeks_left == 15 and ytd.required_weekly_run_rate is not None
    months = b.targets.monthly_revenue
    assert len(months) == 12 and months[0].label == "Jan"
    assert [m.status for m in months].count("future") == 3            # Oct, Nov, Dec
    assert months[8].label == "Sep (MTD)" and months[8].status == "month_to_date"
    assert b.kpis.orders.itpy is not None
    assert b.kpis.return_rate_14d.week_ref == "mature"
    assert b.kpis.cancellation_rate.higher_is_good is False
    assert [s.segment for s in b.cuts.region.orders] == config.REGIONS


def test_spike_raises_anomaly_and_plan_context_flags():
    b = assemble(synthetic_weekly(spike=2.5), synthetic_cuts(), synthetic_plan(), report_weeks(REPORTING), now=NOW)
    ids = {f.id for f in b.flags}
    assert {"anomaly_orders", "plan_context_qtd", "maturity_returns"} <= ids
    assert b.so_what_facts.qtd_attainment_excl_flagged_pct is not None


def test_unmapped_country_fails_quality_gate():
    b = assemble(synthetic_weekly(), synthetic_cuts(countries=("China", "Atlantis")), synthetic_plan(),
                 report_weeks(REPORTING), now=NOW)
    gate = {c.name: c for c in b.data_quality.checks}["all_countries_mapped"]
    assert not gate.passed and "Atlantis" in gate.detail
    assert not b.data_quality.all_passed


def test_brief_is_not_built_before_week_ends():
    early = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)  # Sunday, week still running
    b = assemble(synthetic_weekly(), synthetic_cuts(), synthetic_plan(), report_weeks(REPORTING), now=early)
    assert not {c.name: c for c in b.data_quality.checks}["reporting_week_complete"].passed


def test_region_mapping_covers_local_language_names():
    df, unmapped = map_regions(pd.DataFrame({"week_start": [REPORTING] * 2, "country": ["España", "Deutschland"],
                                             "traffic_source": ["Search"] * 2, "orders": [1, 1], "revenue": [1.0, 1.0]}))
    assert unmapped == [] and set(df["region"]) == {"EMEA"}


def test_extra_fields_are_rejected():
    from weekly_report.models import QualityCheck
    with pytest.raises(Exception):
        QualityCheck(name="x", passed=True, detail="y", surprise=1)


def test_split_facts_totals_match_cuts():
    from weekly_report.brief import split_facts
    facts = pd.DataFrame([
        {"week_start": REPORTING, "country": "China", "traffic_source": "Search", "orders": 10, "cancelled_orders": 1,
         "non_cancelled_orders": 9, "returned_14d_orders": 1, "revenue": 900.0, "new_signups": 4},
        {"week_start": REPORTING, "country": "France", "traffic_source": "Email", "orders": 5, "cancelled_orders": 0,
         "non_cancelled_orders": 5, "returned_14d_orders": 0, "revenue": 500.0, "new_signups": 2},
        {"week_start": REPORTING, "country": "Japan", "traffic_source": "Display", "orders": 0, "cancelled_orders": 0,
         "non_cancelled_orders": 0, "returned_14d_orders": 0, "revenue": 0.0, "new_signups": 3},   # signups only
        {"week_start": REPORTING - timedelta(weeks=30), "country": "China", "traffic_source": "Search", "orders": 7,
         "cancelled_orders": 0, "non_cancelled_orders": 7, "returned_14d_orders": 0, "revenue": 700.0, "new_signups": 1},
    ])
    weekly, cuts = split_facts(facts, report_weeks(REPORTING))
    row = weekly.set_index("week_start").loc[REPORTING]
    assert row["orders"] == 15 and row["new_signups"] == 9 and row["revenue"] == 1400.0
    assert cuts["orders"].sum() == 15                      # cuts add up to the weekly total
    assert set(cuts["week_start"]) == {REPORTING}          # week 30 back is not a compared week
    assert "Japan" not in set(cuts["country"])             # signup-only rows are not order cuts


def test_report_renders_every_layout_section(tmp_path, monkeypatch):
    import yaml
    from weekly_report import render
    from weekly_report.brief import add_kpis
    from weekly_report.pipeline import RunData

    weeks = report_weeks(REPORTING)
    cuts, _ = map_regions(synthetic_cuts())
    run = RunData(weeks, add_kpis(synthetic_weekly()), cuts, synthetic_plan(),
                  assemble(synthetic_weekly(), synthetic_cuts(), synthetic_plan(), weeks, now=NOW), 0, True, NOW)
    monkeypatch.setattr(render, "SITE_DIR", tmp_path)
    monkeypatch.setattr(render, "REPORTS_DIR", tmp_path / "reports")
    html = render.render(run).read_text()
    layout = yaml.safe_load(config.LAYOUT_FILE.read_text())
    for section in layout["sections"]:
        if section.get("title"):
            assert section["title"] in html
    assert "cache hit" in html and (tmp_path / "index.html").exists()
