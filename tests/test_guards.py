"""Each blocking guard must catch its failure, and clean commentary must pass."""

import copy

import yaml

from test_brief import NOW, REPORTING, synthetic_cuts, synthetic_targets, synthetic_weekly
from weekly_report import config
from weekly_report.brief import assemble
from weekly_report.guards import run_guards
from weekly_report.weeks import report_weeks

LAYOUT = yaml.safe_load(config.LAYOUT_FILE.read_text())


def brief(spike: float = 1.0):
    return assemble(synthetic_weekly(spike), synthetic_cuts(), synthetic_targets(), report_weeks(REPORTING), now=NOW)


def clean(b) -> dict:
    k, t = b.kpis, b.targets
    o = f"{k.orders.value:,.0f}"
    wk = f"{b.meta.mature_week.start.day} {b.meta.mature_week.start:%b}"
    pt = lambda w, s: {"what": w, "so_what": s}
    return {
        "summary": {"headline": f"Orders reached {o} this week.",
                    "points": [pt(f"Orders were {o}.", "The week kept its footing."),
                               pt(f"Revenue was ${k.revenue.value:,.0f}.", "Revenue held its level."),
                               pt(f"Signups were {k.new_signups.value:,.0f}.", "Acquisition was stable.")]},
        "watchouts": {"points": []},
        "vs_target": {"points": [pt(f"Orders were {t.orders_vs_target.attainment_pct}% of target.", "The week finished ahead of target."),
                                 pt(f"Revenue was {t.revenue_vs_target.attainment_pct}% of target.", "Revenue is on course.")]},
        "drivers": {"points": [pt(f"APAC orders were {b.cuts.region.orders[0].value:,.0f}.", "APAC is the largest region."),
                               pt(f"Search orders were {b.cuts.traffic_source.orders[0].value:,.0f}.", "Search leads.")]},
        "health": {"points": [pt(f"The cancellation rate was {k.cancellation_rate.value}%.", "Cancellations are stable."),
                              pt(f"The 14-Day Return Rate for the week of {wk} was {k.return_rate_14d.value}%.", "Returns are stable."),
                              pt(f"Average order value was ${k.aov.value:,.2f}.", "Basket size held.")]},
    }


def failed(report) -> set[str]:
    return {c.name for c in report.checks if not c.passed}


def test_clean_commentary_passes():
    b = brief()
    r = run_guards(clean(b), b, LAYOUT)
    assert r.passed, r.summary()


def test_invented_number_is_blocked():
    b = brief(); c = clean(b)
    c["summary"]["points"][0]["what"] = "Orders were 123,456."
    assert "numbers exist in the brief" in failed(run_guards(c, b, LAYOUT))


def test_wrong_direction_is_blocked():
    b = brief(); c = clean(b)
    word = "fell" if b.kpis.orders.wow_direction == "up" and b.kpis.orders.yoy_direction == "up" else "rose"
    c["summary"]["points"][0]["what"] = f"Orders {word} this week."
    assert "direction words match the data" in failed(run_guards(c, b, LAYOUT))


def test_banned_phrases_are_blocked_but_flag_explanations_are_not():
    b = brief()
    for text in ("Orders rose because of a campaign.", "We should increase spend.", "Revenue beat plan."):
        c = clean(b); c["summary"]["points"][0]["so_what"] = text
        assert "no causes, recommendations, 'plan', or 'net revenue'" in failed(run_guards(c, b, LAYOUT)), text
    c = clean(b); c["summary"]["points"][0]["so_what"] = "It is flagged because the value is outside its range."
    assert "no causes, recommendations, 'plan', or 'net revenue'" not in failed(run_guards(c, b, LAYOUT))


def test_return_rate_without_its_week_is_blocked():
    b = brief(); c = clean(b)
    c["health"]["points"][1]["what"] = f"The 14-Day Return Rate was {b.kpis.return_rate_14d.value}%."
    assert "14-Day Return Rate names its mature week" in failed(run_guards(c, b, LAYOUT))


def test_anomaly_must_be_mentioned():
    b = brief(spike=2.5)
    assert any(f.type == "anomaly" for f in b.flags)
    c = clean(b)
    assert "anomaly flag acknowledged in the summary" in failed(run_guards(c, b, LAYOUT))
    c["summary"]["points"][0]["so_what"] = "The jump is flagged as unusual."
    assert "anomaly flag acknowledged in the summary" not in failed(run_guards(c, b, LAYOUT))


def test_warnings_do_not_block():
    b = brief(); c = copy.deepcopy(clean(b))
    c["drivers"]["points"][0]["what"] = "The cancellation rate was " + f"{b.kpis.cancellation_rate.value}% " + "and " * 30
    r = run_guards(c, b, LAYOUT)
    assert r.passed and {"each slot only covers its allowed KPIs", "sentences at most 30 words and 4 numbers"} <= failed(r)


def test_regressions_from_real_runs_2026_09_25():
    """Sentences Claude actually wrote that were wrongly blocked. They must now pass."""
    b = brief()
    down = [s.segment for s in b.cuts.region.orders + b.cuts.traffic_source.orders if s.contribution < 0]
    up = [s.segment for s in b.cuts.region.orders + b.cuts.traffic_source.orders if s.contribution > 0]
    c = clean(b)
    if down:
        c["drivers"]["points"][0]["so_what"] = f"Almost half the growth came from one region, while {down[0]} slipped."
    c["summary"]["points"][1]["so_what"] = "This week sits above the recent pattern, so it should not be read as the normal weekly level."
    assert run_guards(c, b, LAYOUT).passed
    # ...but a real contradiction on a segment is still caught, and real advice is still blocked
    c = clean(b); c["drivers"]["points"][0]["what"] = f"{up[0]} orders fell this week."
    assert "direction words match the data" in failed(run_guards(c, b, LAYOUT))
    c = clean(b); c["drivers"]["points"][0]["so_what"] = "The team should increase Search spend."
    assert "no causes, recommendations, 'plan', or 'net revenue'" in failed(run_guards(c, b, LAYOUT))


def test_behind_target_months_are_not_a_false_alarm():
    b = brief()
    behind = [m for m in b.targets.monthly_revenue if m.variance and m.variance < 0]
    c = clean(b)
    c["vs_target"]["points"][1]["so_what"] = "Earlier months were behind target, later months ahead."
    r = run_guards(c, b, LAYOUT)
    assert ("ahead/behind target matches the data" in failed(r)) == (not behind)


def test_regressions_from_golden_run_v1():
    """False alarms from the first golden run (2026-09-25). Real calculated numbers must still be caught."""
    b = brief()
    region = b.cuts.region.orders
    grew = next(s.segment for s in region if s.contribution > 0)
    fell = [s.segment for s in region if s.contribution < 0]
    allowed = [
        f"The 14-Day Return Rate is reported for the mature week of {b.meta.mature_week.start:%d %b %Y} because the two most recent weeks are not yet mature.",
        "Returns matter because gross revenue does not subtract returns.",
        "Revenue fell faster than orders as a result of the lower value per order.",
        "The week fell short of target even though orders finished ahead of their own target.",
        f"{grew}'s gain is what kept the overall order decline small.",
        "The two largest regions held up, so the shortfall sits elsewhere.",
        "The largest region pulled the total down and was offset by gains elsewhere, leaving orders broadly flat.",
    ]
    for text in allowed:
        c = clean(b); c["summary"]["points"][0]["so_what"] = text
        assert run_guards(c, b, LAYOUT).passed, (text, run_guards(c, b, LAYOUT).summary())
    for text in ("Orders rose because of a spring campaign.", "Revenue grew due to a price increase."):
        c = clean(b); c["summary"]["points"][0]["so_what"] = text
        assert not run_guards(c, b, LAYOUT).passed, text
    c = clean(b); c["summary"]["points"][0]["what"] = "Revenue was 9.87% short of the weekly target."
    assert "numbers exist in the brief" in failed(run_guards(c, b, LAYOUT))


def test_regressions_from_golden_run_v2_prompt():
    """False alarms from prompt v2's new wording (2026-09-26). Real claims must still be caught."""
    from weekly_report.guards import check_target_status
    b = brief()
    statuses = {b.targets.orders_vs_target.status, b.targets.revenue_vs_target.status,
                b.targets.qtd_revenue_vs_target.status, b.targets.ytd_revenue_vs_target.status}
    allowed = [
        "The quarter opens behind, so later weeks have to run above target to close the gap.",
        "Recovering the quarter would require later weeks to run above target, not merely reach it.",
        "No month has been ahead of target this year.",
        "Growth below the target rate keeps attainment under 100%.",
    ]
    for text in allowed:
        c = clean(b); c["vs_target"]["points"][0]["so_what"] = text
        r = run_guards(c, b, LAYOUT)
        assert {"numbers exist in the brief", "ahead/behind target matches the data"}.isdisjoint(failed(r)), (text, r.summary())
    if "ahead" not in statuses:
        c = clean(b); c["vs_target"]["points"][0]["so_what"] = "The week finished ahead of target."
        assert not check_target_status(c, b).passed


def test_order_quality_is_not_order_volume():
    """Replay 2026-07-13: 'order quality is weaker' was checked against order volume (false alarm)."""
    b = brief(); c = clean(b)
    c["health"]["points"][2]["so_what"] = "Order quality is weaker than a year ago even as volume grows strongly."
    assert "direction words match the data" not in failed(run_guards(c, b, LAYOUT))


def test_contrast_sentences_about_a_segment_are_left_to_the_judge():
    """Replay 2026-08-03: 'the gain came despite LATAM' was read as LATAM growing (false alarm)."""
    b = brief(); c = clean(b)
    fell = next((s.segment for s in b.cuts.region.orders if s.contribution < 0), None)
    if fell:
        c["drivers"]["points"][0]["so_what"] = f"One region pulled against the increase, so the gain came despite {fell}."
        assert "direction words match the data" not in failed(run_guards(c, b, LAYOUT))


def test_order_quality_next_to_another_kpi_is_mixed():
    """Regression found while fixing the replay: must stay allowed (golden v2, week of 2026-04-20)."""
    b = brief(); c = clean(b)
    c["health"]["points"][0]["so_what"] = "Order quality on that week improved, a counterweight to the rising cancellation rate."
    assert "direction words match the data" not in failed(run_guards(c, b, LAYOUT))
