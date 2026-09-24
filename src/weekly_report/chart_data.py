"""Chart series for the report page. Kept out of the data brief: the LLM never sees this.

Each chart component in report_layout.yaml gets one entry, keyed by its id, shaped for the
generic JS renderers in the template (line, cumulative, waterfall, bar).
"""

from datetime import date, timedelta

import pandas as pd

from . import config
from .pipeline import RunData
from .weeks import month_of, quarter_of, same_week_last_year


def _weeks_back(end: date, n: int) -> list[date]:
    return [end - timedelta(weeks=i) for i in range(n - 1, -1, -1)]


def _series(df: pd.DataFrame, weeks: list[date], col: str) -> list[float | None]:
    return [None if w not in df.index or pd.isna(df.at[w, col]) else float(df.at[w, col]) for w in weeks]


def _quarter_bands(weeks: list[date]) -> list[dict]:
    bands = {}
    for w in weeks:
        bands.setdefault(quarter_of(w)[1], []).append(w)
    return [{"x0": ws[0].isoformat(), "x1": (ws[-1] + timedelta(days=7)).isoformat(), "label": f"Q{q}", "shade": q % 2 == 1}
            for q, ws in bands.items()]


def fiscal_year_line(comp: dict, run: RunData) -> dict:
    """Actual to date vs the full-year target, Jan to Dec."""
    kpi, fy = comp["kpi"], run.weeks.fy_weeks
    actual = [v if w <= run.weeks.reporting else None for w, v in zip(fy, _series(run.kpis, fy, kpi))]
    out = {"type": "line", "x": [w.isoformat() for w in fy], "unit": kpi,
           "series": [{"name": "Actual", "y": actual, "role": "actual"},
                      {"name": "Target", "y": [float(run.plan.at[w, f"{kpi}_target"]) for w in fy], "role": "target"}]}
    if comp.get("quarter_bands"):
        out["bands"] = _quarter_bands(fy)
    if comp.get("mark_report_week"):
        out["marker"] = {"x": (run.weeks.reporting + timedelta(days=3)).isoformat(), "label": "Report week"}
    return out


def itpy_chart(comp: dict, run: RunData) -> dict:
    """Index to prior year for each KPI: value / same week last year x 100."""
    fy = [w for w in run.weeks.fy_weeks if w <= run.weeks.reporting]
    series = []
    for i, kpi in enumerate(comp["kpis"]):
        cur, ly = _series(run.kpis, fy, kpi), _series(run.kpis, [same_week_last_year(w) for w in fy], kpi)
        series.append({"name": comp_name(kpi), "y": [round(100 * c / l, 1) if c and l else None for c, l in zip(cur, ly)],
                       "role": "actual" if i == 0 else "actual2"})
    return {"type": "line", "x": [w.isoformat() for w in fy], "unit": "index", "series": series,
            "reference": {"y": 100 + config.PLAN_GROWTH_PCT, "label": f"Plan index {100 + config.PLAN_GROWTH_PCT:.0f}"},
            "bands": _quarter_bands(fy)}


def comp_name(kpi: str) -> str:
    return {"orders": "Weekly Orders Placed", "revenue": "Weekly Gross Revenue"}.get(kpi, kpi)


def _month_plan_full(run: RunData, month: str) -> float:
    y, m = map(int, month.split("-"))
    return float(sum(run.plan.at[w, "revenue_target"] for w in run.weeks.fy_weeks if month_of(w) == (y, m)))


def variance_waterfall(comp: dict, run: RunData) -> dict:
    """YTD plan -> monthly variance (actual - plan) -> YTD actual."""
    months = [m for m in run.brief.targets.monthly_revenue if m.status != "future"]
    ytd = run.brief.targets.ytd_revenue_vs_target
    return {"type": "waterfall", "mode": "variance", "unit": comp["kpi"],
            "start": {"label": "YTD plan", "value": ytd.target_to_date},
            "steps": [{"label": m.label, "value": m.variance} for m in months],
            "end": {"label": "YTD actual", "value": ytd.actual}}


def bridge_waterfall(comp: dict, run: RunData) -> dict:
    """YTD actual -> remaining months at plan -> FY outlook, compared with the FY plan."""
    months = run.brief.targets.monthly_revenue
    ytd = run.brief.targets.ytd_revenue_vs_target
    steps = []
    for m in months:
        if m.status == "month_to_date":
            rest = _month_plan_full(run, m.month) - m.plan
            if rest > 0:
                steps.append({"label": f"Rest of {m.label.split(' ')[0]}", "value": rest})
        elif m.status == "future":
            steps.append({"label": m.label, "value": m.plan})
    outlook = ytd.actual + sum(s["value"] for s in steps)
    return {"type": "waterfall", "mode": "bridge", "unit": comp["kpi"],
            "start": {"label": "YTD actual", "value": ytd.actual},
            "steps": steps, "end": {"label": "FY outlook at plan", "value": outlook},
            "reference": {"y": ytd.full_year_plan, "label": f"FY plan ${ytd.full_year_plan / 1e6:.2f}M"},
            "note": (f"To hit the FY plan: ${ytd.required_weekly_run_rate:,.0f} per week for the remaining {ytd.weeks_left} weeks "
                     f"vs ${ytd.current_8wk_run_rate:,.0f} per week over the last 8 weeks")
                    if ytd.required_weekly_run_rate else None}


def line_chart(comp: dict, run: RunData) -> dict:
    if comp.get("period") == "fiscal_year":
        return fiscal_year_line(comp, run)
    kpi, n = comp["kpi"], comp.get("weeks", 52)
    end = run.weeks.mature if kpi == "return_rate_14d" else run.weeks.reporting
    hist = _weeks_back(run.weeks.reporting, n)
    actual = [v if w <= end else None for w, v in zip(hist, _series(run.kpis, hist, kpi))]
    out = {"type": "line", "x": [w.isoformat() for w in hist],
           "series": [{"name": "This year" if comp.get("compare_last_year") else "Actual", "y": actual, "role": "actual"}],
           "unit": kpi}
    if comp.get("compare_last_year"):
        ly = [same_week_last_year(w) for w in hist]
        out["series"].append({"name": "Last year", "y": _series(run.kpis, ly, kpi), "role": "reference"})
    if comp.get("show_target"):
        col = f"{kpi}_target"
        out["series"].append({"name": "Target", "y": [float(run.plan.at[w, col]) if w in run.plan.index else None for w in hist],
                              "role": "target"})
        if comp.get("show_future_target"):
            future = [w for w in run.plan.index if w > run.weeks.reporting]
            out["x"] += [w.isoformat() for w in future]
            for s in out["series"]:
                s["y"] += [None] * len(future)
            out["series"].append({"name": "Future target",
                                  "y": [None] * (len(hist) - 1) + [out["series"][-1]["y"][len(hist) - 1]]
                                       + [float(run.plan.at[w, col]) for w in future],
                                  "role": "future"})
    if comp.get("mark_today"):
        out["marker"] = {"x": (run.weeks.reporting + timedelta(days=3)).isoformat(), "label": "Report week"}
    return out


def cumulative_chart(comp: dict, run: RunData) -> dict:
    qw = run.weeks.quarter_weeks
    done = [w for w in qw if w <= run.weeks.reporting]
    actual = run.kpis.loc[done, comp["kpi"]].cumsum().tolist()
    plan = run.plan.loc[qw, f"{comp['kpi']}_target"].cumsum().tolist()
    return {"type": "line", "x": [w.isoformat() for w in qw], "unit": comp["kpi"],
            "series": [{"name": "Actual (cumulative)", "y": actual + [None] * (len(qw) - len(done)), "role": "actual", "markers": True},
                       {"name": "Plan (cumulative, to quarter end)", "y": plan, "role": "target"}]}


def waterfall(comp: dict, run: RunData) -> dict:
    segs = getattr(run.brief.cuts, comp["cut"]).orders
    return {"type": "waterfall", "mode": "variance", "unit": comp["kpi"],
            "start": {"label": "Prior week", "value": sum(s.prior_week for s in segs)},
            "steps": [{"label": s.segment, "value": s.contribution} for s in segs],
            "end": {"label": "Reporting week", "value": sum(s.value for s in segs)}}


def bar_chart(comp: dict, run: RunData) -> dict:
    labels, values = [], []
    for cut in comp["cuts"]:
        prefix = "Region" if cut == "region" else "Traffic"
        for s in getattr(run.brief.cuts, cut).orders:
            labels.append(f"{prefix} · {s.segment}")
            values.append(s.yoy_pct)
    return {"type": "bar", "labels": labels, "values": values, "reference": config.PLAN_GROWTH_PCT}


BUILDERS = {"line_chart": line_chart, "cumulative_chart": cumulative_chart, "waterfall": waterfall, "bar_chart": bar_chart,
            "itpy_chart": itpy_chart, "variance_waterfall": variance_waterfall, "bridge_waterfall": bridge_waterfall}
CHART_TYPES = set(BUILDERS)


def component_id(section_id: str, comp: dict) -> str:
    return comp.get("id") or f"{section_id}_{comp.get('kpi', comp['type'])}"


def build(layout: dict, run: RunData) -> dict:
    charts = {}
    for section in layout["sections"]:
        for comp in section["components"]:
            if comp["type"] in BUILDERS:
                charts[component_id(section["id"], comp)] = BUILDERS[comp["type"]](comp, run)
    return charts
