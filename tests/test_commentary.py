"""Orchestration: pass, retry, fallback, errors, cache. Claude is replaced by a fake generate()."""

import pytest

from test_brief import NOW, REPORTING, synthetic_cuts, synthetic_targets, synthetic_weekly
from test_guards import clean
from weekly_report import commentary as cm
from weekly_report import config
from weekly_report.brief import assemble
from weekly_report.llm import LLMError, LLMResult
from weekly_report.weeks import report_weeks


@pytest.fixture
def brief(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "COMMENTARY_DIR", tmp_path / "commentary")
    monkeypatch.setattr(config, "RUNS_DIR", tmp_path / "runs")
    return assemble(synthetic_weekly(), synthetic_cuts(), synthetic_targets(), report_weeks(REPORTING), now=NOW)


def fake(outputs):
    """generate() stand-in returning the given commentaries (or raising) in order; records feedback."""
    calls = []

    def generate(brief, version, model, feedback=None):
        calls.append(feedback)
        out = outputs[len(calls) - 1]
        if isinstance(out, Exception):
            raise out
        return LLMResult(commentary=out, prompt_version=version, model=model, backend="fake",
                         duration_ms=1000, cost_usd=0.05, tokens={"input": 10, "output": 5})
    generate.calls = calls
    return generate


def wrong_number(b):
    c = clean(b)
    c["summary"]["points"][0]["what"] = "Orders were 123,456."
    return c


def test_verified_first_time(brief):
    g = fake([clean(brief)])
    o = cm.produce(brief, generate=g)
    assert o.status == "verified" and len(o.attempts) == 1 and o.commentary


def test_retry_gets_feedback_and_recovers(brief):
    g = fake([wrong_number(brief), clean(brief)])
    o = cm.produce(brief, generate=g)
    assert o.status == "verified_after_retry" and len(o.attempts) == 2
    assert "123,456" in g.calls[1]            # the retry was told what failed
    assert o.cost_usd == 0.10                 # both attempts are counted


def test_fallback_never_publishes_wrong_text(brief):
    o = cm.produce(brief, generate=fake([wrong_number(brief), wrong_number(brief)]))
    assert o.status == "fallback" and o.commentary is None


def test_claude_errors_fall_back(brief):
    o = cm.produce(brief, generate=fake([LLMError("timeout"), LLMError("timeout")]))
    assert o.status == "fallback" and all(a.error for a in o.attempts)


def test_unchanged_brief_reuses_cached_commentary(brief):
    cm.produce(brief, generate=fake([clean(brief)]))
    never = fake([])
    o = cm.produce(brief, generate=never)
    assert o.cache_hit and not never.calls


def test_run_log_line_written(brief):
    import json
    o = cm.produce(brief, generate=fake([clean(brief)]))
    cm.log_run(brief, o, bytes_billed=31_000_000)
    line = json.loads((config.RUNS_DIR / "run_log.jsonl").read_text().splitlines()[-1])
    assert line["status"] == "verified" and line["bigquery_mb"] == 31 and line["checks_total"] == 10
