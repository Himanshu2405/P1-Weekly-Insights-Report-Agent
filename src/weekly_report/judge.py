"""LLM judge: scores a week's commentary against its answer key and four quality rules.

Guards answer "is it safe to publish?" (plain code). The judge answers "is it good?" (needs judgement).
"""

import json
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from . import config, llm
from .guards import run_guards
from .models import DataBrief

JUDGE_VERSION = "judge_v4"
QUALITY_RULES = ["headline_has_verdict", "watchouts_are_risks", "no_speculation"]
SLOTS = ["summary", "watchouts", "vs_target", "drivers", "health"]
ANSWER_KEYS = config.ROOT / "evals" / "golden" / "answer_keys.yaml"


class Verdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    kind: Literal["must_say", "must_not_say", "quality"]
    verdict: Literal["pass", "fail"]
    evidence: str = Field(max_length=400)
    reason: str = Field(max_length=300)


class SoWhatVerdict(BaseModel):
    """One so_what, judged on its own: does it say what the fact means?"""
    model_config = ConfigDict(extra="forbid")
    slot: Literal["summary", "watchouts", "vs_target", "drivers", "health"]
    point: int = Field(ge=1)
    verdict: Literal["implication", "restatement"]
    reason: str = Field(max_length=300)


class JudgeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdicts: list[Verdict]
    so_whats: list[SoWhatVerdict]


def answer_keys() -> dict[str, dict]:
    return {str(k["week"]): k for k in yaml.safe_load(ANSWER_KEYS.read_text())}


def published_commentary(saved: dict, brief: DataBrief) -> tuple[Optional[dict], str]:
    """The commentary that would be published under the current guards (first attempt that passes).

    Returns (commentary, status). Re-checking lets old runs be scored with today's guards.
    """
    layout = yaml.safe_load(config.LAYOUT_FILE.read_text())
    attempts = [a for a in saved["attempts"] if a.get("commentary")]
    for i, a in enumerate(attempts):
        if run_guards(a["commentary"], brief, layout).passed:
            return a["commentary"], "verified" if i == 0 else "verified_after_retry"
    return None, "fallback"


def schema() -> dict:
    s = JudgeOutput.model_json_schema()
    defs = s.pop("$defs", {})
    s["properties"]["verdicts"]["items"] = defs["Verdict"]
    s["properties"]["so_whats"]["items"] = defs["SoWhatVerdict"]
    return s


def brief_for_judge(brief: DataBrief) -> dict:
    """The parts of the brief a judge needs to check claims (numbers, comparisons, flags), without run metadata."""
    d = brief.model_dump(mode="json")
    return {"reporting_week": d["meta"]["reporting_week"], "mature_week": d["meta"]["mature_week"],
            "target_growth_pct": d["meta"]["target_growth_pct"], "kpis": d["kpis"], "targets": d["targets"],
            "cuts": d["cuts"], "history_8wk": d["history_8wk"], "flags": d["flags"], "so_what_facts": d["so_what_facts"]}


def user_message(key: dict, commentary: dict, brief: Optional[DataBrief] = None) -> str:
    items = {"must_say": [{"id": i["id"], "text": i["text"]} for i in key["must_say"]],
             "must_not_say": [{"id": i["id"], "text": i["text"]} for i in key["must_not_say"]],
             "quality_rules": QUALITY_RULES}
    context = f"Data brief (for checking claims only):\n{json.dumps(brief_for_judge(brief))}\n\n" if brief else ""
    return (f"Week of {key['week']} ({key['scenario']}).\n\n{context}"
            f"Answer key and rules to judge (return one verdict for each id):\n{json.dumps(items, indent=1)}\n\n"
            f"Commentary:\n{json.dumps(commentary, indent=1)}")


def judge(key: dict, commentary: dict, model: str = config.LLM_MODEL,
          brief: Optional[DataBrief] = None) -> tuple[list[dict], list[dict], llm.LLMResult]:
    system = (config.PROMPTS_DIR / f"{JUDGE_VERSION}.md").read_text()
    result = llm.call_structured(system, user_message(key, commentary, brief), schema(), model, JUDGE_VERSION)
    parsed = JudgeOutput(**result.commentary)
    expected = {i["id"] for i in key["must_say"] + key["must_not_say"]} | set(QUALITY_RULES)
    got = {v.id for v in parsed.verdicts}
    if not expected <= got:
        raise llm.LLMError(f"judge is missing ids {sorted(expected - got)}")
    # Sonnet 5 occasionally adds one extra, unrequested id; keep only what was asked for rather than
    # discarding the whole (otherwise valid) judgement over a stray addition.
    verdicts = [v for v in parsed.verdicts if v.id in expected]

    points = {(s, i) for s in SLOTS for i in range(1, len(commentary[s]["points"]) + 1)}
    judged = {(w.slot, w.point) for w in parsed.so_whats}
    if not points <= judged:
        raise llm.LLMError(f"judge is missing so_whats for {sorted(points - judged)}")
    so_whats = [w for w in parsed.so_whats if (w.slot, w.point) in points]
    return [v.model_dump() for v in verdicts], [w.model_dump() for w in so_whats], result
