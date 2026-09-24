"""Chart series for the report page. Kept out of the data brief: the LLM never sees this.

Each chart component in report_layout.yaml gets one entry, keyed by its id, shaped for the
generic JS renderers in the template (line, cumulative, waterfall, bar).
"""

from datetime import date, timedelta

import pandas as pd

from . import config
from .pipeline import RunData
from .weeks import same_week_last_year


def _weeks_back(end: date, n: int) -> list[date]:
    return [end - timedelta(weeks=i) for i in range(n - 1, -1, -1)]


def _series(df: pd.DataFrame, weeks: list[date], col: str) -> list[float | None]:
    return [None if w not in df.index or pd.isna(df.at[w, col]) else float(df.at[w, col]) for w in weeks]


def line_chart(comp: dict, run: RunData) -> dict:
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
        out["today"] = (run.weeks.reporting + timedelta(days=7)).isoformat()
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
    prior_total = sum(s.prior_week for s in segs)
    return {"type": "waterfall", "prior_total": prior_total, "now_total": sum(s.value for s in segs),
            "labels": [s.segment for s in segs], "deltas": [s.contribution for s in segs]}


def bar_chart(comp: dict, run: RunData) -> dict:
    labels, values = [], []
    for cut in comp["cuts"]:
        prefix = "Region" if cut == "region" else "Traffic"
        for s in getattr(run.brief.cuts, cut).orders:
            labels.append(f"{prefix} · {s.segment}")
            values.append(s.yoy_pct)
    return {"type": "bar", "labels": labels, "values": values, "reference": config.PLAN_GROWTH_PCT}


BUILDERS = {"line_chart": line_chart, "cumulative_chart": cumulative_chart, "waterfall": waterfall, "bar_chart": bar_chart}


def component_id(section_id: str, comp: dict) -> str:
    return comp.get("id") or f"{section_id}_{comp.get('kpi', comp['type'])}"


def build(layout: dict, run: RunData) -> dict:
    charts = {}
    for section in layout["sections"]:
        for comp in section["components"]:
            if comp["type"] in BUILDERS:
                charts[component_id(section["id"], comp)] = BUILDERS[comp["type"]](comp, run)
    return charts
