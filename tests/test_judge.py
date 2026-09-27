"""Judge plumbing (no Claude calls): which commentary gets judged, the schema, the scorecard."""

import json
import sys
from pathlib import Path

from test_guards import brief, clean
from weekly_report.judge import QUALITY_RULES, answer_keys, published_commentary, schema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from judge_golden import scorecard  # noqa: E402


def test_published_commentary_is_first_attempt_that_passes_current_guards():
    b = brief()
    bad = clean(b); bad["summary"]["points"][0]["what"] = "Orders were 123,456."
    good = clean(b)
    assert published_commentary({"attempts": [{"commentary": good}]}, b) == (good, "verified")
    assert published_commentary({"attempts": [{"commentary": bad}, {"commentary": good}]}, b) == (good, "verified_after_retry")
    assert published_commentary({"attempts": [{"commentary": bad}, {"commentary": None}]}, b) == (None, "fallback")


def test_schema_is_self_contained_and_keys_cover_16_weeks():
    assert "$ref" not in json.dumps(schema())
    assert len(answer_keys()) == 16


def test_scorecard_counts():
    rows = [{"week": "w1", "so_whats": [{"slot": "summary", "point": 1, "verdict": "implication", "reason": ""},
                                        {"slot": "summary", "point": 2, "verdict": "restatement", "reason": ""}], "verdicts": [
        {"id": "a", "kind": "must_say", "verdict": "pass"}, {"id": "b", "kind": "must_say", "verdict": "fail"},
        {"id": "c", "kind": "must_not_say", "verdict": "pass"},
        *[{"id": q, "kind": "quality", "verdict": "fail" if q == "headline_has_verdict" else "pass"} for q in QUALITY_RULES]]}]
    s = scorecard(rows, "t")
    assert s["must_say"] == {"passed": 1, "total": 2} and s["must_not_say"] == {"passed": 1, "total": 1}
    assert s["quality"]["headline_has_verdict"] == {"passed": 0, "total": 1}
    assert s["fails_by_week"] == {"w1": ["b", "headline_has_verdict"]}
    assert s["so_whats"]["implication"] == 1 and s["so_whats"]["total"] == 2


def test_judge_tolerates_one_extra_hallucinated_id():
    """Sonnet 5 sometimes adds a stray id (regression from the 2026-09-27 run). Extras are dropped, not fatal."""
    import weekly_report.judge as jmod

    key = {"week": "w1", "scenario": "s", "must_say": [{"id": "a", "text": "t"}], "must_not_say": []}
    commentary = {"summary": {"headline": "h", "points": [{"what": "w", "so_what": "s"}]},
                  "watchouts": {"points": []}, "vs_target": {"points": []}, "drivers": {"points": []}, "health": {"points": []}}
    fake_output = {
        "verdicts": [{"id": "a", "kind": "must_say", "verdict": "pass", "evidence": "", "reason": ""},
                     *[{"id": q, "kind": "quality", "verdict": "pass", "evidence": "", "reason": ""} for q in jmod.QUALITY_RULES],
                     {"id": "sw1", "kind": "quality", "verdict": "pass", "evidence": "", "reason": ""}],
        "so_whats": [{"slot": "summary", "point": 1, "verdict": "implication", "reason": ""}],
    }

    class FakeResult:
        commentary = fake_output
        model = "claude-sonnet-5"
        cost_usd = 0.01
        duration_ms = 100

    orig = jmod.llm.call_structured
    jmod.llm.call_structured = lambda *a, **k: FakeResult()
    try:
        verdicts, so_whats, _ = jmod.judge(key, commentary)
    finally:
        jmod.llm.call_structured = orig
    assert {v["id"] for v in verdicts} == {"a", *jmod.QUALITY_RULES}
    assert len(so_whats) == 1
