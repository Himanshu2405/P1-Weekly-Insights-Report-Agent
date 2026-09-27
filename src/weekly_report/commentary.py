"""Steps 8 to 10 wired together: generate -> guards -> retry once -> fallback -> log.

A wrong number is never published: if the blocking guards still fail after one retry (or Claude
errors twice), the page shows "commentary unavailable" and the numbers are published without AI text.
"""

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import yaml
from pydantic import ValidationError

from . import config, llm
from .guards import GuardReport, run_guards
from .models import DataBrief

MAX_ATTEMPTS = 2  # first try + one retry


@dataclass
class Attempt:
    number: int
    ok: bool                      # True when the blocking guards passed
    error: Optional[str] = None   # Claude/CLI error or broken output format
    duration_ms: int = 0
    cost_usd: float = 0.0
    tokens: dict = field(default_factory=dict)
    blocking_failures: list[str] = field(default_factory=list)
    guard_details: dict = field(default_factory=dict)       # failed check -> what it caught
    commentary: Optional[dict] = None                         # kept even when rejected, for error analysis


@dataclass
class CommentaryOutcome:
    status: str                   # verified | verified_after_retry | fallback
    commentary: Optional[dict]    # None when status is fallback
    guard_report: Optional[dict]  # checks from the final attempt
    prompt_version: str
    model: str
    backend: str
    attempts: list[Attempt]
    brief_hash: str
    cache_hit: bool = False

    @property
    def cost_usd(self) -> float:
        return round(sum(a.cost_usd for a in self.attempts), 4)

    @property
    def duration_ms(self) -> int:
        return sum(a.duration_ms for a in self.attempts)

    @property
    def tokens(self) -> dict:
        total: dict = {}
        for a in self.attempts:
            for k, v in a.tokens.items():
                total[k] = total.get(k, 0) + v
        return total

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(cost_usd=self.cost_usd, duration_ms=self.duration_ms, tokens=self.tokens)
        return d


def brief_hash(brief: DataBrief) -> str:
    """Fingerprint of the brief's content (ignores run id, timestamps and check wording)."""
    d = brief.model_dump(mode="json")
    d["meta"] = {k: v for k, v in d["meta"].items() if k not in ("run_id", "generated_at_utc")}
    d.pop("data_quality", None)
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def _feedback(report: GuardReport) -> str:
    return "\n".join(f"- {c.name}: {d}" for c in report.blocking_failures for d in c.details)


def _cache_file(week: str, version: str, out_dir: Optional[Path] = None) -> Path:
    return (out_dir or config.COMMENTARY_DIR) / f"commentary_{week}_{version}.json"


def produce(brief: DataBrief, version: str = config.PROMPT_VERSION, model: str = config.LLM_MODEL,
            use_cache: bool = True, generate: Callable = llm.generate,
            out_dir: Optional[Path] = None) -> CommentaryOutcome:
    """out_dir: where the commentary file is saved (default: commentary/; evals use their own folder)."""
    layout = yaml.safe_load(config.LAYOUT_FILE.read_text())
    week, h = brief.meta.reporting_week.start.isoformat(), brief_hash(brief)

    # cache: same brief content + same prompt + same model -> reuse, no Claude call
    cached = _cache_file(week, version, out_dir)
    if use_cache and cached.exists():
        saved = json.loads(cached.read_text())
        if saved.get("brief_hash") == h and saved.get("model") == model and saved.get("status") != "fallback":
            saved["attempts"] = [Attempt(**a) for a in saved["attempts"]]
            saved = {k: v for k, v in saved.items() if k in CommentaryOutcome.__dataclass_fields__}
            return CommentaryOutcome(**{**saved, "cache_hit": True})

    attempts: list[Attempt] = []
    feedback, report, result = None, None, None
    for n in range(1, MAX_ATTEMPTS + 1):
        try:
            result = generate(brief, version=version, model=model, feedback=feedback)
        except (llm.LLMError, ValidationError, json.JSONDecodeError, TimeoutError, subprocess.TimeoutExpired) as e:
            attempts.append(Attempt(n, ok=False, error=f"{type(e).__name__}: {str(e)[:300]}"))
            feedback = None
            continue
        report = run_guards(result.commentary, brief, layout)
        attempts.append(Attempt(n, ok=report.passed, duration_ms=result.duration_ms, cost_usd=result.cost_usd,
                                tokens=result.tokens, blocking_failures=[c.name for c in report.blocking_failures],
                                guard_details={c.name: c.details for c in report.checks if not c.passed},
                                commentary=result.commentary))
        if report.passed:
            break
        feedback = _feedback(report)

    ok = bool(attempts and attempts[-1].ok)
    outcome = CommentaryOutcome(
        status=("verified" if len(attempts) == 1 else "verified_after_retry") if ok else "fallback",
        commentary=result.commentary if ok else None,
        guard_report=report.to_dict() if report else None,
        prompt_version=version, model=result.model if result else model,
        backend=result.backend if result else "claude_headless", attempts=attempts, brief_hash=h,
    )
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps({"week": week, **outcome.to_dict()}, indent=2))
    return outcome


def log_run(brief: DataBrief, outcome: CommentaryOutcome, bytes_billed: int) -> None:
    """Append one line per run to runs/run_log.jsonl (the observability record)."""
    checks = (outcome.guard_report or {}).get("checks", [])
    entry = {
        "logged_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "week": brief.meta.reporting_week.start.isoformat(),
        "brief_run_id": brief.meta.run_id,
        "brief_hash": outcome.brief_hash,
        "status": outcome.status,
        "cache_hit": outcome.cache_hit,
        "prompt_version": outcome.prompt_version,
        "model": outcome.model,
        "backend": outcome.backend,
        "attempts": len(outcome.attempts),
        "llm_cost_usd": outcome.cost_usd,
        "llm_duration_ms": outcome.duration_ms,
        "tokens": outcome.tokens,
        "bigquery_mb": round(bytes_billed / 1e6),
        "checks_passed": sum(c["passed"] for c in checks),
        "checks_total": len(checks),
        "blocking_failures": [c["name"] for c in checks if c["severity"] == "block" and not c["passed"]],
        "warnings": {c["name"]: c["details"] for c in checks if c["severity"] == "warn" and not c["passed"]},
        "errors": [a.error for a in outcome.attempts if a.error],
    }
    config.RUNS_DIR.mkdir(exist_ok=True)
    with (config.RUNS_DIR / "run_log.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
