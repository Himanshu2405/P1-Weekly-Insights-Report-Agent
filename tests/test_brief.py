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
    weeks = [REPORTING + timedelta(weeks=i) for i in range(-20, 10)]
    return pd.DataFrame({"week_start": weeks, "orders_target": 1000, "revenue_target": 85000}).set_index("week_start")


def test_brief_validates_and_passes_quality():
    b = assemble(synthetic_weekly(), synthetic_cuts(), synthetic_plan(), report_weeks(REPORTING), now=NOW)
    assert b.data_quality.all_passed
    assert b.meta.reporting_week.week_of_quarter == 12
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
