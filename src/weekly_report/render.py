"""Render the static HTML report from the layout file, the data brief, and chart data."""

import json
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import chart_data, config
from .pipeline import RunData

TEMPLATES_DIR = config.ROOT / "templates"
SITE_DIR = config.ROOT / "site"
REPORTS_DIR = SITE_DIR / "reports"


# ---------------------------------------------------------------- formatting

def fmt(value, kind: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    if kind == "count":
        return f"{value:,.0f}"
    if kind == "usd":
        return f"-${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"
    if kind == "usd_cents":
        return f"${value:,.2f}"
    if kind == "percent":
        return f"{value:.1f}%"
    return str(value)


def fmt_change(change, unit: str) -> str:
    if change is None:
        return "n/a"
    sign = "+" if change > 0 else "−" if change < 0 else ""
    return f"{sign}{abs(change):.1f}{' pp' if unit == 'pp' else '%'}"


def fmt_signed(value, kind: str) -> str:
    return ("+" if value > 0 else "") + fmt(value, kind)


def sparkline(values: list[float | None]) -> str:
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pts) < 2:
        return ""
    w, h, p = 96, 32, 3
    vs = [v for _, v in pts]
    lo, hi = min(vs), max(vs)
    span = (hi - lo) or 1
    xy = [(p + i * (w - 2 * p) / (len(values) - 1), h - p - (v - lo) / span * (h - 2 * p)) for i, v in pts]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    lx, ly = xy[-1]
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" aria-hidden="true"><polyline fill="none" stroke="var(--s1)" '
            f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="{line}"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="3" fill="var(--s1)"/></svg>')


# ---------------------------------------------------------------- page pieces

def kpi_cards(run: RunData, layout: dict) -> list[dict]:
    b, reg = run.brief, layout["kpis"]
    cards = []
    for key, k in b.kpis.model_dump().items():
        end = run.weeks.mature if k["week_ref"] == "mature" else run.weeks.reporting
        last8 = [end - timedelta(weeks=i) for i in range(7, -1, -1)]
        foot = (f"Week of {end:%b %-d} (latest mature week)" if k["week_ref"] == "mature"
                else f"Prior week {fmt(k['prior_week'], k['format'])} · Last year {fmt(k['last_year'], k['format'])}")
        cards.append({
            "name": reg[key]["name"], "value": fmt(k["value"], k["format"]),
            "deltas": [(fmt_change(k["wow_change"], k["change_unit"]) + " WoW", k["wow_assessment"], k["wow_direction"]),
                       (fmt_change(k["yoy_change"], k["change_unit"]) + " YoY", k["yoy_assessment"], k["yoy_direction"])],
            "spark": sparkline([run.kpis.at[w, key] if w in run.kpis.index else None for w in last8]),
            "foot": foot,
        })
    t = b.targets
    for key, tgt, kind in (("orders_vs_target", t.orders_vs_target, "count"), ("revenue_vs_target", t.revenue_vs_target, "usd")):
        col = "orders" if kind == "count" else "revenue"
        weeks8 = [run.weeks.reporting - timedelta(weeks=i) for i in range(7, -1, -1)]
        att = [100 * run.kpis.at[w, col] / run.plan.at[w, f"{col}_target"] if w in run.plan.index and w in run.kpis.index else None
               for w in weeks8]
        cards.append({
            "name": reg[key]["name"], "value": f"{tgt.attainment_pct:.1f}%",
            "deltas": [(f"{fmt_signed(tgt.gap, kind)} vs target", "good" if tgt.gap >= 0 else "bad", "up" if tgt.gap >= 0 else "down")],
            "spark": sparkline(att),
            "foot": f"Target {fmt(tgt.target, kind)} · Next week {fmt(tgt.next_week_target, kind)}",
        })
    q = t.qtd_revenue_vs_target
    done = [w for w in run.weeks.quarter_weeks if w <= run.weeks.reporting]
    cum_a = run.kpis.loc[done, "revenue"].cumsum()
    cum_p = run.plan.loc[done, "revenue_target"].cumsum()
    cards.append({
        "name": reg["qtd_revenue_vs_target"]["name"], "value": f"{q.attainment_pct:.1f}%",
        "deltas": [(f"{fmt_signed(q.gap, 'usd')} vs plan", "good" if q.gap >= 0 else "bad", "up" if q.gap >= 0 else "down")],
        "spark": sparkline((100 * cum_a / cum_p).tolist()[-8:]),
        "foot": f"Full-quarter plan {fmt(q.full_quarter_plan, 'usd')} · {q.weeks_left} week{'s' if q.weeks_left != 1 else ''} left",
    })
    return cards


def tiles(run: RunData) -> list[dict]:
    t = run.brief.targets
    return [
        {"label": "Weekly Orders vs target", "pct": t.orders_vs_target.attainment_pct,
         "detail": f"{fmt(t.orders_vs_target.actual, 'count')} orders vs target {fmt(t.orders_vs_target.target, 'count')}",
         "next": f"Next week's target: {fmt(t.orders_vs_target.next_week_target, 'count')} orders"},
        {"label": "Weekly Gross Revenue vs target", "pct": t.revenue_vs_target.attainment_pct,
         "detail": f"{fmt(t.revenue_vs_target.actual, 'usd')} vs target {fmt(t.revenue_vs_target.target, 'usd')}",
         "next": f"Next week's target: {fmt(t.revenue_vs_target.next_week_target, 'usd')}"},
        {"label": "Quarter-to-date revenue vs plan", "pct": t.qtd_revenue_vs_target.attainment_pct,
         "detail": f"{fmt(t.qtd_revenue_vs_target.actual, 'usd')} vs plan {fmt(t.qtd_revenue_vs_target.target_to_date, 'usd')}",
         "next": f"Full-quarter plan: {fmt(t.qtd_revenue_vs_target.full_quarter_plan, 'usd')} "
                 f"({t.qtd_revenue_vs_target.weeks_left} week{'s' if t.qtd_revenue_vs_target.weeks_left != 1 else ''} left)"},
    ]


def code_watchouts(run: RunData, layout: dict) -> list[dict]:
    """Deterministic text for code-detected flags. AI notes are added in Phase 2."""
    names = {k: v["name"] for k, v in layout["kpis"].items()}
    kpis = run.brief.kpis.model_dump()
    out = []
    for f in run.brief.flags:
        x = f.facts
        if f.type == "anomaly":
            kind = kpis[f.kpi]["format"]
            text = f"{names[f.kpi]} is {x['ratio_to_avg']}x its 8-week average ({fmt(x['value'], kind)} vs {fmt(x['avg_8wk'], kind)})."
            label = "Anomaly"
        elif f.type == "streak":
            text = (f"{names[f.kpi]} has moved in the wrong direction {x['weeks']} weeks in a row, "
                    f"from {x['from']:.1f}% to {x['to']:.1f}%.")
            label = "Trend"
        elif f.type == "plan_context":
            text = (f"Excluding the flagged week, quarter-to-date revenue would be {x['qtd_attainment_excl_flagged_pct']:.1f}% "
                    f"of plan instead of {x['qtd_attainment_pct']:.1f}%.")
            label = "Plan context"
        else:
            text = (f"14-Day Return Rate is reported for the week of {pd.Timestamp(x['mature_week_start']):%b %-d}. "
                    f"The {x['immature_weeks']} most recent weeks are not yet mature.")
            label = "Data maturity"
        out.append({"severity": f.severity, "label": label, "text": text, "source": "Detected by code"})
    return out


def segment_table(run: RunData, by: str, order: list[str]) -> list[dict]:
    w = run.weeks
    pv = run.cuts.pivot_table(index=by, columns="week_start", values=["orders", "revenue"], aggfunc="sum", fill_value=0)

    def get(metric, week, seg):
        return float(pv[(metric, week)].get(seg, 0)) if (metric, week) in pv.columns else 0.0

    def pct(a, b):
        return None if not b else round((a / b - 1) * 100, 1)

    rows, tot = [], {k: 0.0 for k in ("o", "op", "ol", "r", "rp", "rl")}
    for seg in order + ["Total"]:
        if seg == "Total":
            o, op, ol, r, rp, rl = (tot[k] for k in ("o", "op", "ol", "r", "rp", "rl"))
        else:
            o, op, ol = (get("orders", x, seg) for x in (w.reporting, w.prior, w.last_year))
            r, rp, rl = (get("revenue", x, seg) for x in (w.reporting, w.prior, w.last_year))
            for k, v in zip(("o", "op", "ol", "r", "rp", "rl"), (o, op, ol, r, rp, rl)):
                tot[k] += v
        rows.append({"segment": seg, "orders": fmt(o, "count"), "orders_wow": fmt_change(pct(o, op), "pct"),
                     "orders_yoy": fmt_change(pct(o, ol), "pct"), "revenue": fmt(r, "usd"),
                     "revenue_wow": fmt_change(pct(r, rp), "pct"), "revenue_yoy": fmt_change(pct(r, rl), "pct"),
                     "orders_now": o, "contribution": fmt_signed(o - op, "count"), "total": seg == "Total"})
    for row in rows:  # shares need the grand total, known only after the loop
        row["share"] = f"{100 * row.pop('orders_now') / tot['o']:.1f}%" if tot["o"] else "n/a"
    return rows


def archive(current: str) -> list[dict]:
    files = sorted(REPORTS_DIR.glob("report_*.html"), reverse=True)
    return [{"href": p.name, "label": f"Week of {pd.Timestamp(p.stem[7:]):%b %-d, %Y}"}
            for p in files if p.stem[7:] != current][: 8]


# ---------------------------------------------------------------- render

def render(run: RunData) -> Path:
    layout = yaml.safe_load(config.LAYOUT_FILE.read_text())
    b, w = run.brief, run.weeks
    for section in layout["sections"]:
        for comp in section["components"]:
            comp["_id"] = chart_data.component_id(section["id"], comp)
            if comp.get("kpi") and not comp.get("title"):
                comp["title"] = layout["kpis"][comp["kpi"]]["name"] + (" (%)" if layout["kpis"][comp["kpi"]]["format"] == "percent" else "")

    et = run.run_at.astimezone(ZoneInfo("America/New_York"))
    year, q = w.quarter
    context = {
        "layout": layout,
        "page_title": layout["page"]["title"],
        "week_label": (f"Reporting week: Mon {w.reporting:%b %-d} to Sun {w.reporting + timedelta(days=6):%b %-d, %Y} "
                       f"(Q{q}, week {w.week_of_quarter} of {len(w.quarter_weeks)})"),
        "published": f"Built {et:%a %-d %b %Y, %-I:%M %p} ET",
        "data_through": f"Data through Sun {w.reporting + timedelta(days=6):%-d %b %Y}",
        "quality": b.data_quality,
        "tiles": tiles(run),
        "kpi_cards": kpi_cards(run, layout),
        "watchouts": code_watchouts(run, layout),
        "tables": {"region": segment_table(run, "region", config.REGIONS),
                   "traffic_source": segment_table(run, "traffic_source", config.TRAFFIC_SOURCES)},
        "run": {"run_id": b.meta.run_id, "bytes": "0 MB (cache hit)" if run.cache_hit else f"{run.bytes_billed / 1e6:.0f} MB", "target_version": b.meta.target_version,
                "brief_version": b.brief_version, "layout_version": b.meta.layout_version},
        "archive": archive(w.reporting.isoformat()),
        "charts_json": json.dumps(chart_data.build(layout, run)),
        "kpi_formats_json": json.dumps({k: v["format"] for k, v in layout["kpis"].items()}),
    }
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html", "j2"]))
    html = env.get_template("report.html.j2").render(**context)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"report_{w.reporting.isoformat()}.html"
    out.write_text(html)
    (SITE_DIR / "index.html").write_text(html.replace('href="report_', 'href="reports/report_'))
    return out
