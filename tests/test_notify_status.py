"""The status-comment summary must not misattribute a stale log entry to the current run."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import notify_status  # noqa: E402


def write_log(tmp_path, monkeypatch, minutes_old, **fields):
    log = tmp_path / "run_log.jsonl"
    entry = {"logged_at_utc": (datetime.now(timezone.utc) - timedelta(minutes=minutes_old)).isoformat(),
             "status": "verified", "attempts": 1, "checks_passed": 10, "checks_total": 10,
             "llm_cost_usd": 0.0734, **fields}
    log.write_text(json.dumps(entry) + "\n")
    monkeypatch.setattr(notify_status, "RUN_LOG", str(log))


def test_fresh_entry_is_summarized(tmp_path, monkeypatch):
    write_log(tmp_path, monkeypatch, minutes_old=2)
    summary = notify_status.fresh_run_summary()
    assert "verified" in summary
    assert "10/10" in summary
    assert "0.0734" in summary


def test_stale_entry_is_not_attributed_to_this_run(tmp_path, monkeypatch):
    write_log(tmp_path, monkeypatch, minutes_old=90)
    assert "No fresh run log entry" in notify_status.fresh_run_summary()


def test_missing_log_file(tmp_path, monkeypatch):
    monkeypatch.setattr(notify_status, "RUN_LOG", str(tmp_path / "does_not_exist.jsonl"))
    assert "No fresh run log entry" in notify_status.fresh_run_summary()
