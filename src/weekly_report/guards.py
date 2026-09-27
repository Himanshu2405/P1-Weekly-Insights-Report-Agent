"""Step 9: guards. Plain-code checks on the AI commentary before anything is published.

Two severities:
- block: publishing this would put something wrong in front of leadership (wrong number, wrong
  direction, banned claim, missing required caveat). Any block failure -> retry, then fallback.
- warn: quality issues (too long, too dense, repeated, off-topic for the slot). Logged and shown in
  the eval results; they do not stop publishing.
"""

import re
from dataclasses import dataclass, field

from .models import DataBrief

# ---------------------------------------------------------------- vocabulary

KPI_WORDS = {
    # "order quality", "order value", "average order value" are about AOV/cancellations, not order volume
    "orders": [r"(?<!average )\borders?\b(?!\s+(quality|value|size|mix))"],
    "revenue": [r"\brevenue\b"],
    "aov": [r"average order value", r"\baov\b"],
    "cancellation_rate": [r"cancell?ation"],
    "return_rate_14d": [r"return rate", r"14-day return", r"\breturns?\b"],
    "new_signups": [r"sign-?ups?\b"],
}
UP_WORDS = r"\b(rose|rise|rising|up|increased?|increasing|grew|grow|growing|higher|gained?)\b"
DOWN_WORDS = r"\b(fell|fall|falling|down|decreased?|decreasing|declined?|declining|dropped|drop|lower|slipped|edged down)\b"
GOOD_WORDS = r"\b(improved|improvement|better|healthier)\b"
BAD_WORDS = r"\b(worsened|worse|deteriorated|weaker)\b"
AHEAD_WORDS = r"\b(ahead of|above|beat|beaten|exceeded|over) (the )?(\w+ )?target"
BEHIND_WORDS = r"\b(behind|below|missed|short of|under) (the )?(\w+ )?target"
BANNED = {
    # Business causes only. Bare "because" is allowed: it is used to explain data ("reported for 16 Mar because the
    # two most recent weeks are not mature") or definitions, which are facts, not causes. Arithmetic like
    # "as a result of the lower value per order" (revenue = orders x AOV) is also allowed.
    "causal claim": r"\b(because of|due to|thanks to|caused by|owing to|led to|as a result of (a|an|the|our|their)? ?(campaign|promotion|sale|discount|marketing|price|pricing|holiday|season|launch|competitor|outage|email|ad)s?|driven by (a|the) (campaign|promotion|price|sale|discount))\b",
    # "should not be read as..." is reading guidance; only flag "should/must + business action" and explicit advice
    "recommendation": r"\b((should|must|need to|ought to) (increase|decrease|invest|cut|focus|prioriti[sz]e|shift|reduce|boost|add|launch|run|expand|lower|raise|push|double)|we recommend|recommend(ed|s)? (that|to|increasing|reducing)|consider (increasing|reducing|investing|shifting|cutting))\b",
    "says plan or budget": r"\b(plan|plans|budget)\b",
    "calls revenue net": r"\bnet revenue\b",
}
MONTHS = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
DATE_PATTERNS = [rf"\b\d{{1,2}} {MONTHS} \d{{4}}\b", rf"\b{MONTHS} \d{{1,2}}(, \d{{4}})?\b", r"\b\d{4}-\d{2}-\d{2}\b",
                 rf"\b\d{{1,2}} {MONTHS}\b", r"\b20\d{2}\b", r"\bQ[1-4]\b"]
NUMBER = r"(?<![\w.])[-−]?\$?\d[\d,]*(?:\.\d+)?"
REFERENCE_NUMBERS = {100.0}   # "under 100% of target" is a reference line, not a data point
# "have to run above target", "would need to finish ahead of target": a requirement, not a claim
REQUIREMENT = r"\b(have|has|had|need|needs|needed|would need|must|required|require|requires|to) (to )?(run|be|come in|finish|land|stay|get|move)\b[^.]{0,20}$"
NEGATION = r"\b(no|not|never|none|nor|without)\b[^.]{0,40}$"
MAX_WORDS = 30
MAX_NUMBERS_PER_SENTENCE = 4


# ---------------------------------------------------------------- results

@dataclass
class Check:
    name: str
    severity: str            # "block" or "warn"
    passed: bool = True
    details: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.passed = False
        self.details.append(msg)


@dataclass
class GuardReport:
    checks: list[Check]

    @property
    def passed(self) -> bool:
        """True when no blocking check failed (warnings allowed)."""
        return all(c.passed for c in self.checks if c.severity == "block")

    @property
    def blocking_failures(self) -> list[Check]:
        return [c for c in self.checks if c.severity == "block" and not c.passed]

    def summary(self) -> str:
        lines = [f"{'PASS' if self.passed else 'BLOCKED'}: "
                 f"{sum(c.passed for c in self.checks)} of {len(self.checks)} checks passed"]
        for c in self.checks:
            lines.append(f"  [{'x' if c.passed else ' '}] {c.name} ({c.severity})")
            lines += [f"      - {d}" for d in c.details[:6]]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"passed": self.passed, "checks": [c.__dict__ for c in self.checks]}


# ---------------------------------------------------------------- helpers

def _items(commentary: dict) -> list[tuple[str, str, str]]:
    """(slot, label, text) for every headline, what, and so_what."""
    out = []
    for slot, body in commentary.items():
        if body.get("headline"):
            out.append((slot, "headline", body["headline"]))
        for i, p in enumerate(body.get("points", []), 1):
            out.append((slot, f"point {i} what", p["what"]))
            out.append((slot, f"point {i} so_what", p["so_what"]))
    return out


def _strip_dates(text: str) -> str:
    for pat in DATE_PATTERNS:
        text = re.sub(pat, " ", text)
    return text


def _numbers(text: str) -> list[str]:
    return re.findall(NUMBER, _strip_dates(text))


def _brief_values(brief: DataBrief) -> set[float]:
    """Every number in the brief, including numbers written inside its strings."""
    vals: set[float] = set()

    def walk(x):
        if isinstance(x, bool) or x is None:
            return
        if isinstance(x, (int, float)):
            vals.add(abs(float(x)))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            for n in re.findall(r"\d+(?:\.\d+)?", x):
                vals.add(float(n))

    walk(brief.model_dump(mode="json"))
    return vals


def _matches_brief(token: str, values: set[float]) -> bool:
    clean = token.replace("$", "").replace(",", "").replace("−", "-").lstrip("-")
    num = float(clean)
    if num in REFERENCE_NUMBERS:
        return True
    decimals = len(clean.split(".")[1]) if "." in clean else 0
    return any(round(v, decimals) == num for v in values)


def _kpis_in(text: str) -> set[str]:
    t = text.lower()
    found = {k for k, pats in KPI_WORDS.items() if any(re.search(p, t) for p in pats)}
    if re.search(r"\border quality\b", t):
        found.add("order_quality")  # a subject of its own (AOV, cancellations, returns), so the sentence is mixed
    return found


# ---------------------------------------------------------------- checks

def check_numbers(commentary: dict, brief: DataBrief) -> Check:
    c = Check("numbers exist in the brief", "block")
    values = _brief_values(brief)
    for slot, label, text in _items(commentary):
        for tok in _numbers(text):
            if not _matches_brief(tok, values):
                c.fail(f"{slot} {label}: '{tok}' is not in the brief")
    return c


YOY_WORDS = r"\b(last year|a year ago|yoy|year on year|year-over-year|prior year|75%|target growth|growth the targets assume)\b"
TARGET_GAP_WORDS = r"\b(target|short of|shortfall|gap)\b"
IDIOMS = r"\b(held up|up to|up with|down to earth|kept .{0,30}? to)\b"  # "held up", "kept the decline to 4 orders"
TOTAL_WORDS = r"\b(total|overall|in all|combined)\b"
CONTRAST_WORDS = r"\b(despite|against|while|whereas|offset|offsetting|but|although|even as|counterweight)\b"  # "the gain came despite LATAM"
SEGMENT_REFS = r"\b(regions?|sources?|segments?|channels?|markets?)\b"  # "the largest region" without naming it


def _segment_moves(brief: DataBrief) -> dict[str, tuple[float, float]]:
    """Segment name -> (WoW change in orders, YoY % change) for region and traffic-source sentences."""
    return {s.segment.lower(): (s.contribution, s.yoy_pct or 0.0)
            for cut in (brief.cuts.region, brief.cuts.traffic_source) for s in cut.orders}


def check_directions(commentary: dict, brief: DataBrief) -> Check:
    """Direction and good/bad words must agree with the brief.

    Only unambiguous sentences are judged here (mixed sentences go to the LLM judge):
    - one segment named, no total/overall and no target-gap wording: checked against that segment
      (YoY sign if the sentence talks about last year or target growth, otherwise the WoW change);
    - exactly one KPI, no segment and no target-gap wording: checked against that KPI's WoW and YoY.
    """
    c = Check("direction words match the data", "block")
    kpis = brief.kpis.model_dump()
    segments = _segment_moves(brief)
    for slot, label, text in _items(commentary):
        t = re.sub(IDIOMS, " ", text.lower())
        if re.search(TARGET_GAP_WORDS, t):
            continue  # "fell short of target" is about the target gap; the target-status guard covers it
        says_up, says_down = bool(re.search(UP_WORDS, t)), bool(re.search(DOWN_WORDS, t))
        named = [seg for seg in segments if re.search(rf"\b{re.escape(seg)}\b", t)]
        if named:
            if len(named) > 1 or re.search(TOTAL_WORDS, t) or re.search(CONTRAST_WORDS, t) or (says_up and says_down):
                continue  # mixed sentence: leave it to the judge
            wow, yoy = segments[named[0]]
            move = yoy if re.search(YOY_WORDS, t) else wow
            if says_down and move > 0:
                c.fail(f"{slot} {label}: says down, but {named[0]} grew")
            if says_up and move < 0:
                c.fail(f"{slot} {label}: says up, but {named[0]} fell")
            continue
        if re.search(SEGMENT_REFS, t):
            continue  # talks about an unnamed segment: leave it to the judge
        mentioned = _kpis_in(t)
        if len(mentioned) != 1 or "order_quality" in mentioned:
            continue  # several subjects, or "order quality" (not a single KPI): leave it to the judge
        k = kpis[mentioned.pop()]
        dirs = {k["wow_direction"], k["yoy_direction"]}
        assessments = {k["wow_assessment"], k["yoy_assessment"]}
        if says_up and not says_down and "up" not in dirs:
            c.fail(f"{slot} {label}: says up, but {k['name']} is {k['wow_direction']} WoW and {k['yoy_direction']} YoY")
        if says_down and not says_up and "down" not in dirs:
            c.fail(f"{slot} {label}: says down, but {k['name']} is {k['wow_direction']} WoW and {k['yoy_direction']} YoY")
        if re.search(GOOD_WORDS, t) and "good" not in assessments:
            c.fail(f"{slot} {label}: says better, but the change in {k['name']} is bad for the business")
        if re.search(BAD_WORDS, t) and "bad" not in assessments:
            c.fail(f"{slot} {label}: says worse, but the change in {k['name']} is good for the business")
    return c


def check_target_status(commentary: dict, brief: DataBrief) -> Check:
    c = Check("ahead/behind target matches the data", "block")
    t = brief.targets
    statuses = {t.orders_vs_target.status, t.revenue_vs_target.status, t.qtd_revenue_vs_target.status,
                t.ytd_revenue_vs_target.status}
    # months can be ahead or behind too ("Jan to Apr were behind target")
    statuses |= {"ahead" if m.variance > 0 else "behind" for m in t.monthly_revenue if m.variance}
    def claims(pattern: str, low: str) -> bool:
        """True if the sentence asserts ahead/behind, ignoring requirements ("have to run above target")
        and negations ("no month ahead of target")."""
        for m in re.finditer(pattern, low):
            before = low[:m.start()]
            if re.search(REQUIREMENT, before) or re.search(NEGATION, before):
                continue
            return True
        return False

    for slot, label, text in _items(commentary):
        low = text.lower()
        if claims(AHEAD_WORDS, low) and "ahead" not in statuses:
            c.fail(f"{slot} {label}: says ahead of target, but no target is ahead")
        if claims(BEHIND_WORDS, low) and "behind" not in statuses and "short of what" not in low:
            c.fail(f"{slot} {label}: says behind target, but no target is behind")
    return c


def check_banned(commentary: dict) -> Check:
    c = Check("no causes, recommendations, 'plan', or 'net revenue'", "block")
    for slot, label, text in _items(commentary):
        for why, pat in BANNED.items():
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                c.fail(f"{slot} {label}: {why} ('{m.group(0)}')")
    return c


def check_return_week(commentary: dict, brief: DataBrief) -> Check:
    c = Check("14-Day Return Rate names its mature week", "block")
    start = brief.meta.mature_week.start
    names = [f"{start.day} {start:%b}", f"{start:%b} {start.day}", start.isoformat(), f"{start:%d %b}"]
    for slot, body in commentary.items():
        for i, p in enumerate(body.get("points", []), 1):
            text = f"{p['what']} {p['so_what']}"
            if "return_rate_14d" in _kpis_in(text) and "%" in text and not any(n in text for n in names):
                c.fail(f"{slot} point {i}: mentions the return rate without naming the week of {start:%d %b}")
    return c


def check_anomaly_mentioned(commentary: dict, brief: DataBrief) -> Check:
    c = Check("anomaly flag acknowledged in the summary", "block")
    if any(f.type == "anomaly" for f in brief.flags):
        text = " ".join(t for s, _, t in _items(commentary) if s == "summary").lower()
        if not re.search(r"anomal|unusual|flagged|out of line|irregular", text):
            c.fail("the brief has an anomaly flag, but the summary does not mention it")
    return c


def check_length(commentary: dict) -> Check:
    c = Check(f"sentences at most {MAX_WORDS} words and {MAX_NUMBERS_PER_SENTENCE} numbers", "warn")
    for slot, label, text in _items(commentary):
        words, nums = len(text.split()), len(_numbers(text))
        if words > MAX_WORDS:
            c.fail(f"{slot} {label}: {words} words")
        if nums > MAX_NUMBERS_PER_SENTENCE:
            c.fail(f"{slot} {label}: {nums} numbers")
    return c


def check_slot_scope(commentary: dict, layout: dict) -> Check:
    c = Check("each slot only covers its allowed KPIs", "warn")
    base = {"orders_vs_target": "orders", "revenue_vs_target": "revenue", "qtd_revenue_vs_target": "revenue",
            "ytd_revenue_vs_target": "revenue"}
    for slot, rules in layout["commentary_slots"].items():
        allowed = {base.get(k, k) for k in rules["allowed_kpis"]}
        for s, label, text in _items(commentary):
            if s == slot and not label.endswith("so_what"):  # so-whats may link to other KPIs (e.g. revenue impact)
                extra = _kpis_in(text) - allowed - {"order_quality"}
                if extra:
                    c.fail(f"{slot} {label}: mentions {sorted(extra)}, not allowed in this slot")
    return c


def check_repetition(commentary: dict) -> Check:
    """The same specific number appearing in 3 or more slots means a fact is being repeated."""
    c = Check("no fact repeated across 3+ slots", "warn")
    seen: dict[str, set[str]] = {}
    for slot, _, text in _items(commentary):
        for tok in _numbers(text):
            if "." in tok or "," in tok or tok.startswith("$"):  # skip small integers like '2 weeks'
                seen.setdefault(tok, set()).add(slot)
    for tok, slots in seen.items():
        if len(slots) >= 3:
            c.fail(f"'{tok}' appears in {len(slots)} slots: {sorted(slots)}")
    return c


def check_so_what_not_restating(commentary: dict) -> Check:
    c = Check("so_what differs from what", "warn")
    for slot, body in commentary.items():
        for i, p in enumerate(body.get("points", []), 1):
            a, b = set(p["what"].lower().split()), set(p["so_what"].lower().split())
            if a and b and len(a & b) / len(a | b) > 0.6:
                c.fail(f"{slot} point {i}: so_what mostly repeats what")
    return c


def run_guards(commentary: dict, brief: DataBrief, layout: dict) -> GuardReport:
    return GuardReport([
        check_numbers(commentary, brief),
        check_directions(commentary, brief),
        check_target_status(commentary, brief),
        check_banned(commentary),
        check_return_week(commentary, brief),
        check_anomaly_mentioned(commentary, brief),
        check_length(commentary),
        check_slot_scope(commentary, layout),
        check_repetition(commentary),
        check_so_what_not_restating(commentary),
    ])
