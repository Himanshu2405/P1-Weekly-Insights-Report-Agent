"""Compare two golden-set experiments side by side (e.g. prompt v1 vs v2).

Fair comparison: guard results for both experiments are re-checked with today's guards (older runs may
have used stricter guards), and cost is compared per first attempt as well as in total.

Usage:
    python scripts/compare_experiments.py v1_opus-5 v2_opus-5
"""

import json
import sys

import yaml

from weekly_report import config
from weekly_report.guards import run_guards
from weekly_report.models import DataBrief

EXPERIMENTS = config.ROOT / "evals" / "experiments"
GOLDEN = config.ROOT / "evals" / "golden" / "briefs"


def guard_stats(name: str) -> dict:
    layout = yaml.safe_load(config.LAYOUT_FILE.read_text())
    first_pass = after_retry = fallback = 0
    first_cost, warn_weeks, warnings = [], 0, 0
    for f in sorted((EXPERIMENTS / name).glob("commentary_*.json")):
        saved = json.loads(f.read_text())
        brief = DataBrief.model_validate_json((GOLDEN / f"brief_{saved['week']}.json").read_text())
        attempts = [a for a in saved["attempts"] if a.get("commentary")]
        reports = [run_guards(a["commentary"], brief, layout) for a in attempts]
        if attempts:
            first_cost.append(attempts[0]["cost_usd"])
        if reports and reports[0].passed:
            first_pass += 1
        elif len(reports) > 1 and reports[1].passed:
            after_retry += 1
        else:
            fallback += 1
        published = next((r for r in reports if r.passed), None)
        if published:
            w = [c for c in published.checks if c.severity == "warn" and not c.passed]
            warn_weeks += bool(w)
            warnings += sum(len(c.details) for c in w)
    n = first_pass + after_retry + fallback
    return {"weeks": n, "first_pass": first_pass, "after_retry": after_retry, "fallback": fallback,
            "warn_weeks": warn_weeks, "warnings": warnings,
            "cost_first_attempt": round(sum(first_cost) / len(first_cost), 3) if first_cost else 0}


def row(label: str, a, b, better: str = "higher") -> str:
    def num(x):
        return float(str(x).split()[0].rstrip("%").replace("$", "")) if x not in (None, "") else None
    na, nb = num(a), num(b)
    arrow = ""
    if na is not None and nb is not None and na != nb:
        good = (nb > na) == (better == "higher")
        arrow = " ✅" if good else " ⚠️"
    return f"| {label} | {a} | {b}{arrow} |"


def main(a: str, b: str) -> int:
    ja, jb = (json.loads((EXPERIMENTS / x / "judge_summary.json").read_text()) for x in (a, b))
    ga, gb = guard_stats(a), guard_stats(b)
    sa, sb = (json.loads((EXPERIMENTS / x / "summary.json").read_text()) for x in (a, b))

    def share(p, q):
        return f"{100 * p / q:.0f}% ({p}/{q})" if q else "n/a"

    lines = [f"# {a} vs {b}", "",
             f"Same 16 golden weeks, same answer keys, same judge ({jb['judge']}), guards re-checked with today's rules.", "",
             f"| Measure | {a} | {b} |", "|---|---|---|",
             "| **Quality (LLM judge)** | | |",
             row("Must-say items conveyed", share(ja["must_say"]["passed"], ja["must_say"]["total"]), share(jb["must_say"]["passed"], jb["must_say"]["total"])),
             row("Must-not-say items avoided", share(ja["must_not_say"]["passed"], ja["must_not_say"]["total"]), share(jb["must_not_say"]["passed"], jb["must_not_say"]["total"])),
             row("So-whats that are real implications", share(ja["so_whats"]["implication"], ja["so_whats"]["total"]), share(jb["so_whats"]["implication"], jb["so_whats"]["total"]))]
    for q in ja["quality"]:
        lines.append(row(f"Weeks passing: {q.replace('_', ' ')}", share(ja["quality"][q]["passed"], ja["quality"][q]["total"]),
                         share(jb["quality"][q]["passed"], jb["quality"][q]["total"])))
    lines += ["| **Safety (guards, today's rules)** | | |",
              row("Passed on first attempt", f"{ga['first_pass']} of {ga['weeks']}", f"{gb['first_pass']} of {gb['weeks']}"),
              row("Passed after one retry", ga["after_retry"], gb["after_retry"], "lower"),
              row("Fallback (not published)", ga["fallback"], gb["fallback"], "lower"),
              row("Weeks with warnings", ga["warn_weeks"], gb["warn_weeks"], "lower"),
              row("Warning count (density, repetition, ...)", ga["warnings"], gb["warnings"], "lower"),
              "| **Cost (API equivalent)** | | |",
              row("Average cost of a first attempt", f"${ga['cost_first_attempt']}", f"${gb['cost_first_attempt']}", "lower"),
              row("Judge cost for 16 weeks", f"${ja['judge_cost_usd']}", f"${jb['judge_cost_usd']}", "lower"),
              "", "## So-whats by week (share that are real implications)", "",
              f"| Week | {a} | {b} |", "|---|---|---|"]
    for w in sorted(ja["so_whats"]["by_week"]):
        va, vb = ja["so_whats"]["by_week"][w], jb["so_whats"]["by_week"].get(w, {"implication": 0, "total": 0})
        lines.append(row(w, share(va["implication"], va["total"]), share(vb["implication"], vb["total"])))
    lines += ["", "## Judge failures by week", "", f"| Week | {a} | {b} |", "|---|---|---|"]
    for w in sorted(set(ja["fails_by_week"]) | set(jb["fails_by_week"])):
        lines.append(f"| {w} | {', '.join(ja['fails_by_week'].get(w, [])) or '-'} | {', '.join(jb['fails_by_week'].get(w, [])) or '-'} |")
    lines.append(f"\nRun totals as recorded: {a} ${sa['total_cost_usd']}, {b} ${sb['total_cost_usd']} "
                 f"({a} ran with older, stricter guards, so its recorded total includes avoidable retries).")
    out = EXPERIMENTS / f"compare_{a}_vs_{b}.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
