"""Build the weekly data brief from query results. Everything the LLM may say is computed here.

Split into small functions so each rule can be tested without BigQuery (see tests/).
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import yaml

from . import config, rules
from .models import DataBrief
from .weeks import ReportWeeks

# Display metadata for the 6 core KPIs: (brief key, name, format, higher_is_good, change_unit, week_ref)
KPI_SPECS = [
    ("orders", "Weekly Orders Placed", "count", True, "pct", "reporting"),
    ("revenue", "Weekly Gross Revenue (excl. cancelled)", "usd", True, "pct", "reporting"),
    ("aov", "Weekly Average Order Value", "usd_cents", True, "pct", "reporting"),
    ("cancellation_rate", "Weekly Order Cancellation Rate", "percent", False, "pp", "reporting"),
    ("return_rate_14d", "14-Day Return Rate", "percent", False, "pp", "mature"),
    ("new_signups", "Weekly New Customer Signups", "count", True, "pct", "reporting"),
]
ANOMALY_KPIS = {"orders", "revenue", "aov", "new_signups"}  # ratio rule makes sense for counts and money


# ---------------------------------------------------------------- split the single query result

WEEKLY_COLS = ["orders", "cancelled_orders", "non_cancelled_orders", "returned_14d_orders", "revenue", "new_signups"]


def split_facts(facts: pd.DataFrame, weeks: ReportWeeks) -> tuple[pd.DataFrame, pd.DataFrame]:
    """weekly_facts.sql returns week x country x traffic_source. Turn it into:
    - weekly totals (one row per week) for the KPIs
    - cut rows for the 3 compared weeks (reporting, prior, last year)
    """
    df = facts.copy()
    df["week_start"] = pd.to_datetime(df["week_start"]).dt.date
    weekly = df.groupby("week_start", as_index=False)[WEEKLY_COLS].sum()
    compared = df[df["week_start"].isin([weeks.reporting, weeks.prior, weeks.last_year]) & (df["orders"] > 0)]
    cuts = compared[["week_start", "country", "traffic_source", "orders", "revenue"]].reset_index(drop=True)
    return weekly, cuts


# ---------------------------------------------------------------- weekly KPI table

def add_kpis(weekly: pd.DataFrame) -> pd.DataFrame:
    """Derive rates and AOV, rounded exactly as they will be shown (changes are computed from these)."""
    df = weekly.copy()
    df["week_start"] = pd.to_datetime(df["week_start"]).dt.date
    df["orders"] = df["orders"].astype(int)
    df["new_signups"] = df["new_signups"].astype(int)
    df["revenue"] = df["revenue"].astype(float).round(0)
    df["aov"] = (df["revenue"] / df["non_cancelled_orders"]).round(2)
    df["cancellation_rate"] = (100 * df["cancelled_orders"] / df["orders"]).round(1)
    df["return_rate_14d"] = (100 * df["returned_14d_orders"] / df["orders"]).round(1)
    return df.set_index("week_start").sort_index()


def _val(df: pd.DataFrame, week: date, col: str) -> float | None:
    return float(df.at[week, col]) if week in df.index else None


def build_kpi(df: pd.DataFrame, spec: tuple, weeks: ReportWeeks) -> dict:
    key, name, fmt, higher_is_good, unit, week_ref = spec
    if week_ref == "mature":
        cur, prior, ly = weeks.mature, weeks.mature_prior, weeks.mature_last_year
    else:
        cur, prior, ly = weeks.reporting, weeks.prior, weeks.last_year
    value, prior_v, ly_v = _val(df, cur, key), _val(df, prior, key), _val(df, ly, key)
    previous_8 = [float(v) for v in df.loc[df.index < cur, key].tail(8)]
    wow, yoy = rules.change(value, prior_v, unit), rules.change(value, ly_v, unit)
    notable, reason = rules.is_notable(value, wow, unit, previous_8)
    ratio = rules.anomaly_ratio(value, previous_8) if key in ANOMALY_KPIS else None
    if ratio is not None:
        notable, reason = True, f"anomaly: {ratio}x its 8-week average"
    out = {
        "name": name, "format": fmt, "higher_is_good": higher_is_good, "change_unit": unit, "week_ref": week_ref,
        "value": value, "prior_week": prior_v, "wow_change": wow,
        "wow_direction": rules.direction(wow), "wow_assessment": rules.assessment(wow, higher_is_good),
        "last_year": ly_v, "yoy_change": yoy,
        "yoy_direction": rules.direction(yoy), "yoy_assessment": rules.assessment(yoy, higher_is_good),
        "notable": notable, "notable_reason": reason,
    }
    if key in ("orders", "revenue"):
        out["avg_8wk"] = round(sum(previous_8) / len(previous_8), 0)
    return out


# ---------------------------------------------------------------- targets

def _status(attainment: float) -> str:
    return "on_target" if round(attainment, 1) == 100.0 else ("ahead" if attainment > 100 else "behind")


def build_targets(df: pd.DataFrame, plan: pd.DataFrame, weeks: ReportWeeks) -> dict:
    nxt = weeks.reporting + timedelta(weeks=1)
    out = {}
    for key, col in (("orders_vs_target", "orders"), ("revenue_vs_target", "revenue")):
        actual = _val(df, weeks.reporting, col)
        target = float(plan.at[weeks.reporting, f"{col}_target"])
        att = 100 * actual / target
        out[key] = {
            "actual": actual, "target": target, "attainment_pct": round(att, 1), "gap": round(actual - target, 0),
            "status": _status(att),
            "next_week_target": float(plan.at[nxt, f"{col}_target"]) if nxt in plan.index else None,
        }
    to_date = [w for w in weeks.quarter_weeks if w <= weeks.reporting]
    actual = float(df.loc[to_date, "revenue"].sum())
    target_to_date = float(plan.loc[to_date, "revenue_target"].sum())
    full = float(plan.loc[weeks.quarter_weeks, "revenue_target"].sum())
    att = 100 * actual / target_to_date
    out["qtd_revenue_vs_target"] = {
        "actual": actual, "target_to_date": target_to_date, "attainment_pct": round(att, 1),
        "gap": round(actual - target_to_date, 0), "status": _status(att),
        "full_quarter_plan": full, "remaining_to_full_quarter_plan": round(full - actual, 0),
        "weeks_left": len(weeks.quarter_weeks) - weeks.week_of_quarter,
    }
    return out


# ---------------------------------------------------------------- cuts

def map_regions(cuts: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Add a region column. Returns the unmapped countries so the quality gate can fail on them."""
    df = cuts.copy()
    df["week_start"] = pd.to_datetime(df["week_start"]).dt.date
    df["region"] = df["country"].map(config.REGION_BY_COUNTRY)
    unmapped = sorted(df.loc[df["region"].isna(), "country"].dropna().unique().tolist())
    df["region"] = df["region"].fillna("Unmapped")
    return df, unmapped


def build_segments(cuts: pd.DataFrame, by: str, order: list[str], weeks: ReportWeeks) -> list[dict]:
    pivot = cuts.pivot_table(index=by, columns="week_start", values="orders", aggfunc="sum", fill_value=0)
    now, prior, ly = (pivot.get(w, pd.Series(0, index=pivot.index)) for w in (weeks.reporting, weeks.prior, weeks.last_year))
    total_now, total_change = now.sum(), now.sum() - prior.sum()
    out = []
    for seg in order:
        v, p, l = float(now.get(seg, 0)), float(prior.get(seg, 0)), float(ly.get(seg, 0))
        out.append({
            "segment": seg, "value": v, "prior_week": p, "wow_pct": rules.change(v, p, "pct"),
            "last_year": l, "yoy_pct": rules.change(v, l, "pct"),
            "share_pct": round(100 * v / total_now, 1) if total_now else 0.0,
            "contribution": v - p,
            "share_of_change_pct": round(100 * (v - p) / total_change, 1) if total_change else None,
        })
    return out


# ---------------------------------------------------------------- flags and so-what facts

def build_flags(df: pd.DataFrame, kpis: dict, targets: dict, weeks: ReportWeeks) -> tuple[list[dict], float | None]:
    flags = []
    anomaly_on_plan_kpi = False
    for key in ("orders", "revenue", "aov", "new_signups"):
        k = kpis[key]
        previous_8 = [float(v) for v in df.loc[df.index < weeks.reporting, key].tail(8)]
        ratio = rules.anomaly_ratio(k["value"], previous_8)
        if ratio is not None:
            anomaly_on_plan_kpi |= key in ("orders", "revenue")
            flags.append({"id": f"anomaly_{key}", "type": "anomaly", "severity": "serious", "kpi": key,
                          "facts": {"value": k["value"], "avg_8wk": round(sum(previous_8) / len(previous_8), 0),
                                    "ratio_to_avg": ratio,
                                    "rule": f"value > {config.ANOMALY_HIGH_RATIO}x or < {config.ANOMALY_LOW_RATIO}x 8-week average"}})

    for key, end_week in (("cancellation_rate", weeks.reporting), ("return_rate_14d", weeks.mature)):
        series = [float(v) for v in df.loc[df.index <= end_week, key].tail(config.STREAK_WEEKS + 3)]
        streak = rules.bad_streak(series, kpis[key]["higher_is_good"])
        if streak >= config.STREAK_WEEKS:
            flags.append({"id": f"streak_{key}", "type": "streak", "severity": "warning", "kpi": key,
                          "facts": {"weeks": streak, "direction": "up" if not kpis[key]["higher_is_good"] else "down",
                                    "from": series[-1 - streak], "to": series[-1],
                                    "rule": f"{config.STREAK_WEEKS}+ consecutive moves in the bad direction"}})

    qtd_excl = None
    if anomaly_on_plan_kpi and weeks.week_of_quarter > 1:
        q = targets["qtd_revenue_vs_target"]
        cur = targets["revenue_vs_target"]
        qtd_excl = round(100 * (q["actual"] - cur["actual"]) / (q["target_to_date"] - cur["target"]), 1)
        flags.append({"id": "plan_context_qtd", "type": "plan_context", "severity": "warning", "kpi": "qtd_revenue_vs_target",
                      "facts": {"qtd_attainment_pct": q["attainment_pct"], "qtd_attainment_excl_flagged_pct": qtd_excl,
                                "rule": "shown when an anomaly flag affects a plan KPI"}})

    flags.append({"id": "maturity_returns", "type": "maturity", "severity": "warning", "kpi": "return_rate_14d",
                  "facts": {"mature_week_start": weeks.mature.isoformat(), "immature_weeks": config.MATURITY_LAG_WEEKS}})
    return flags, qtd_excl


def build_so_what(kpis: dict, targets: dict, cuts: dict, qtd_excl: float | None) -> dict:
    def top(segs):
        t = max(segs, key=lambda s: s["contribution"]) if sum(s["contribution"] for s in segs) >= 0 \
            else min(segs, key=lambda s: s["contribution"])
        return {"segment": t["segment"], "contribution": t["contribution"], "share_of_change_pct": t["share_of_change_pct"]}

    all_segs = cuts["region"]["orders"] + cuts["traffic_source"]["orders"]
    q = targets["qtd_revenue_vs_target"]
    return {
        "next_week_targets": {"orders": targets["orders_vs_target"]["next_week_target"],
                              "revenue": targets["revenue_vs_target"]["next_week_target"]},
        "full_quarter_plan": q["full_quarter_plan"],
        "quarter_remaining_to_plan": q["remaining_to_full_quarter_plan"],
        "qtd_attainment_excl_flagged_pct": qtd_excl,
        "revenue_per_pp_cancellation": round(kpis["orders"]["value"] * 0.01 * kpis["aov"]["value"], 0),
        "avg_8wk": {"orders": kpis["orders"]["avg_8wk"], "revenue": kpis["revenue"]["avg_8wk"]},
        "top_contributor": {"region": top(cuts["region"]["orders"]), "traffic_source": top(cuts["traffic_source"]["orders"])},
        "yoy_vs_plan_growth": {"orders_yoy_pct": kpis["orders"]["yoy_change"], "revenue_yoy_pct": kpis["revenue"]["yoy_change"],
                               "plan_growth_pct": config.PLAN_GROWTH_PCT},
        "signups_vs_orders_growth": {"signups_wow_pct": kpis["new_signups"]["wow_change"], "orders_wow_pct": kpis["orders"]["wow_change"],
                                     "signups_yoy_pct": kpis["new_signups"]["yoy_change"], "orders_yoy_pct": kpis["orders"]["yoy_change"]},
        "segments_all_growing": {
            "wow": all((s["wow_pct"] or 0) > 0 for s in all_segs),
            "yoy": all((s["yoy_pct"] or 0) > 0 for s in all_segs),
            "above_plan_growth": all((s["yoy_pct"] or 0) > config.PLAN_GROWTH_PCT for s in all_segs),
        },
    }


# ---------------------------------------------------------------- data-quality gates

def quality_checks(df: pd.DataFrame, plan: pd.DataFrame, unmapped: list[str], weeks: ReportWeeks, now: datetime) -> list[dict]:
    expected = [weeks.reporting - timedelta(weeks=i) for i in range(9)]
    missing = [w.isoformat() for w in expected if w not in df.index]
    avg8 = df.loc[df.index < weeks.reporting, "orders"].tail(8).mean()
    cur_orders = _val(df, weeks.reporting, "orders") or 0
    nxt = weeks.reporting + timedelta(weeks=1)
    return [
        {"name": "reporting_week_complete", "passed": weeks.data_through < now,
         "detail": f"week ended {weeks.data_through:%Y-%m-%d %H:%M} UTC, run at {now:%Y-%m-%d %H:%M} UTC"},
        {"name": "no_missing_weeks", "passed": not missing,
         "detail": "reporting week and prior 8 weeks present" if not missing else f"missing weeks: {missing}"},
        {"name": "target_rows_present", "passed": weeks.reporting in plan.index and all(w in plan.index for w in weeks.quarter_weeks),
         "detail": f"reporting week and all {len(weeks.quarter_weeks)} quarter weeks found in {config.TARGET_VERSION}"
                   + ("" if nxt in plan.index else "; next week has no target (end of plan year)")},
        {"name": "all_countries_mapped", "passed": not unmapped,
         "detail": "0 unmapped countries" if not unmapped else f"unmapped: {unmapped}"},
        {"name": "row_count_sane", "passed": cur_orders > 0 and cur_orders <= 5 * avg8,
         "detail": f"{int(cur_orders)} orders vs 8-week average {avg8:.0f} (limit: > 0 and <= 5x)"},
        {"name": "mature_week_ready",
         "passed": weeks.mature + timedelta(days=7 + config.RETURN_WINDOW_DAYS) <= weeks.reporting + timedelta(days=7),
         "detail": f"every order in week {weeks.mature} has had {config.RETURN_WINDOW_DAYS} days by {weeks.data_through:%Y-%m-%d}"},
    ]


# ---------------------------------------------------------------- assemble

def assemble(weekly: pd.DataFrame, cuts_raw: pd.DataFrame, plan: pd.DataFrame, weeks: ReportWeeks,
             now: datetime | None = None) -> DataBrief:
    now = now or datetime.now(timezone.utc)
    df = add_kpis(weekly)
    cuts_df, unmapped = map_regions(cuts_raw)

    kpis = {spec[0]: build_kpi(df, spec, weeks) for spec in KPI_SPECS}
    targets = build_targets(df, plan, weeks)
    cuts = {
        "region": {"orders": build_segments(cuts_df, "region", config.REGIONS, weeks)},
        "traffic_source": {"orders": build_segments(cuts_df, "traffic_source", config.TRAFFIC_SOURCES, weeks)},
    }
    flags, qtd_excl = build_flags(df, kpis, targets, weeks)
    checks = quality_checks(df, plan, unmapped, weeks, now)
    hist = df.loc[df.index <= weeks.reporting].tail(8)
    layout_version = str(yaml.safe_load(config.LAYOUT_FILE.read_text())["version"])

    year, q = weeks.quarter
    return DataBrief.model_validate({
        "meta": {
            "run_id": f"{now:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}",
            "generated_at_utc": now,
            "reporting_week": {"start": weeks.reporting, "end": weeks.reporting + timedelta(days=6),
                               "quarter": f"{year}-Q{q}", "week_of_quarter": weeks.week_of_quarter,
                               "weeks_in_quarter": len(weeks.quarter_weeks)},
            "mature_week": {"start": weeks.mature, "end": weeks.mature + timedelta(days=6), "used_for": ["return_rate_14d"]},
            "data_through_utc": weeks.data_through,
            "source": config.SOURCE_DATASET,
            "target_version": config.TARGET_VERSION,
            "layout_version": layout_version,
            "plan_growth_pct": config.PLAN_GROWTH_PCT,
        },
        "data_quality": {"all_passed": all(c["passed"] for c in checks), "checks": checks},
        "kpis": kpis,
        "targets": targets,
        "cuts": cuts,
        "history_8wk": {
            "week_start": list(hist.index),
            "orders": hist["orders"].astype(float).tolist(),
            "cancellation_rate": hist["cancellation_rate"].tolist(),
            "return_rate_14d": [float(v) if w <= weeks.mature else None for w, v in hist["return_rate_14d"].items()],
        },
        "flags": flags,
        "so_what_facts": build_so_what(kpis, targets, cuts, qtd_excl),
    })
