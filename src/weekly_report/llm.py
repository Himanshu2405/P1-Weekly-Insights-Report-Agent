"""Steps 7 and 8: assemble the prompt and call Claude for the commentary.

The model call lives behind `generate()`. Today it runs Claude Code headless (`claude -p`) with the
user's subscription; an Anthropic API backend can be added behind the same function later.
"""

import json
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field

from . import config
from .commentary_schema import commentary_model, json_schema
from .models import DataBrief


# ---------------------------------------------------------------- step 7: assemble the prompt

def system_prompt(version: str = config.PROMPT_VERSION) -> str:
    """Instructions (prompts/commentary_<version>.md) with the business context inserted."""
    template = (config.PROMPTS_DIR / f"commentary_{version}.md").read_text()
    return template.replace("{{business_context}}", config.BUSINESS_CONTEXT_FILE.read_text())


def user_message(brief: DataBrief, feedback: str | None = None) -> str:
    """The data brief, with the reporting week stated explicitly (the CLI also injects today's date)."""
    w = brief.meta.reporting_week
    m = brief.meta.mature_week
    msg = (f"Reporting week: Monday {w.start:%d %b %Y} to Sunday {w.end:%d %b %Y} "
           f"({w.quarter}, week {w.week_of_quarter} of {w.weeks_in_quarter}). "
           f"The 14-Day Return Rate refers to the mature week of {m.start:%d %b %Y}. "
           f"Write the commentary for this week only.\n\n"
           f"Data brief (JSON):\n{brief.model_dump_json(indent=1)}")
    if feedback:  # retry: tell Claude exactly which checks its previous answer failed
        msg += f"\n\nYour previous answer failed these automated checks. Rewrite it and fix every one:\n{feedback}"
    return msg


# ---------------------------------------------------------------- step 8: call Claude

@dataclass
class LLMResult:
    commentary: dict
    prompt_version: str
    model: str
    backend: str
    duration_ms: int
    cost_usd: float                     # API-equivalent cost reported by the CLI
    tokens: dict = field(default_factory=dict)
    session_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class LLMError(RuntimeError):
    pass


def _claude_headless(system: str, user: str, schema: dict, model: str) -> dict:
    """One isolated `claude -p` call: empty folder, no tools, no personal settings, no connectors."""
    cmd = [
        "claude", "-p", user,
        "--system-prompt", system,
        "--json-schema", json.dumps(schema),
        "--model", model,
        "--tools", "",
        "--setting-sources", "",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--output-format", "json",
    ]
    with tempfile.TemporaryDirectory(prefix="commentary_") as empty_dir:
        proc = subprocess.run(cmd, cwd=empty_dir, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              timeout=config.LLM_TIMEOUT_SECONDS)
    if proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip())[:500]
        raise LLMError(f"claude exited with {proc.returncode}: {detail or 'no output'}")
    out = json.loads(proc.stdout)
    if out.get("is_error"):
        raise LLMError(f"claude returned an error: {str(out.get('result'))[:500]}")
    return out


def with_backoff(fn, *args, retries: int = config.LLM_TRANSPORT_RETRIES, base_delay: float = 5.0, sleep=time.sleep):
    """Retry infrastructure failures (CLI crash, timeout, bad JSON) with exponential backoff: 5 s, 10 s, ...

    Content problems (failed guards) are handled separately in commentary.produce(), so a CLI hiccup
    never uses up the one 'fix your text' retry.
    """
    for attempt in range(retries + 1):
        try:
            return fn(*args)
        except (LLMError, subprocess.TimeoutExpired, json.JSONDecodeError):
            if attempt == retries:
                raise
            sleep(base_delay * 2 ** attempt)


def call_structured(system: str, user: str, schema: dict, model: str, version: str) -> LLMResult:
    """One structured Claude call (any prompt): returns the JSON answer plus model, time, cost, tokens."""
    started = time.monotonic()
    out = with_backoff(_claude_headless, system, user, schema, model)
    answer = out.get("structured_output")
    if answer is None:
        raise LLMError("no structured_output in the response")
    u = out.get("usage", {})
    return LLMResult(
        commentary=answer,
        prompt_version=version,
        model=next(iter(out.get("modelUsage") or {model: None})),
        backend="claude_headless",
        duration_ms=int(out.get("duration_ms") or (time.monotonic() - started) * 1000),
        cost_usd=float(out.get("total_cost_usd") or 0.0),
        tokens={"input": u.get("input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0),
                "cache_read": u.get("cache_read_input_tokens", 0), "output": u.get("output_tokens", 0),
                "thinking": (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)},
        session_id=out.get("session_id", ""),
    )


def generate(brief: DataBrief, version: str = config.PROMPT_VERSION, model: str = config.LLM_MODEL,
             feedback: str | None = None) -> LLMResult:
    result = call_structured(system_prompt(version), user_message(brief, feedback), json_schema(), model, version)
    commentary_model()(**result.commentary)  # shape check: raises if Claude broke the output format
    return result
