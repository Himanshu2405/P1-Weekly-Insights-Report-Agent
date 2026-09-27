"""Score an experiment's commentaries with the LLM judge and write the quality scorecard.

Usage:
    python scripts/judge_golden.py --experiment v1_opus-5
    python scripts/judge_golden.py --experiment v1_opus-5 --rejudge     # ignore saved judge results

Writes into evals/experiments/<experiment>/: judge_<week>.json per week, judge_summary.json,
judge_summary.md, and calibration.md (a sample of verdicts for the human to check).
"""

import argparse
import json
import random
import sys
from collections import defaultdict

from weekly_report import config
from weekly_report.judge import JUDGE_VERSION, QUALITY_RULES, answer_keys, judge, published_commentary
from weekly_report.models import DataBrief

EXPERIMENTS = config.ROOT / "evals" / "experiments"
GOLDEN = config.ROOT / "evals" / "golden" / "briefs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--model", default=config.LLM_MODEL)
    parser.add_argument("--rejudge", action="store_true")
    args = parser.parse_args()

    exp = EXPERIMENTS / args.experiment
    keys = answer_keys()
    rows, cost = [], 0.0
    for f in sorted(exp.glob("commentary_*.json")):
        saved = json.loads(f.read_text())
        week = saved["week"]
        out = exp / f"judge_{week}.json"
        if out.exists() and not args.rejudge:
            rows.append(json.loads(out.read_text()))
            print(f"  {week}  (already judged)")
            continue
        brief = DataBrief.model_validate_json((GOLDEN / f"brief_{week}.json").read_text())
        commentary, status = published_commentary(saved, brief)
        if commentary is None:
            row = {"week": week, "status": status, "verdicts": [], "so_whats": [], "cost_usd": 0.0}
        else:
            verdicts, so_whats, res = judge(keys[week], commentary, args.model)
            row = {"week": week, "status": status, "judge": JUDGE_VERSION, "model": res.model, "verdicts": verdicts,
                   "so_whats": so_whats, "cost_usd": res.cost_usd, "duration_s": round(res.duration_ms / 1000, 1)}
            cost += res.cost_usd
        out.write_text(json.dumps(row, indent=2))
        rows.append(row)
        fails = [v["id"] for v in row["verdicts"] if v["verdict"] == "fail"]
        sw = row.get("so_whats", [])
        rate = f"{sum(w['verdict'] == 'implication' for w in sw)}/{len(sw)}" if sw else "-"
        print(f"  {week}  {status:21} so-whats {rate:6} fails: {', '.join(fails) or '-'}  ${row['cost_usd']:.3f}", flush=True)

    summary = scorecard(rows, args.experiment)
    (exp / "judge_summary.json").write_text(json.dumps(summary, indent=2))
    (exp / "judge_summary.md").write_text(to_markdown(summary))
    (exp / "calibration.md").write_text(calibration_sheet(rows, args.experiment))
    print(f"\nMust-say {summary['must_say']['passed']}/{summary['must_say']['total']} | "
          f"must-not avoided {summary['must_not_say']['passed']}/{summary['must_not_say']['total']} | "
          + f"so-whats implication {summary['so_whats']['implication']}/{summary['so_whats']['total']} | "
          + " | ".join(f"{r} {q['passed']}/{q['total']}" for r, q in summary["quality"].items())
          + f" | judge cost this run ${cost:.3f}")
    return 0


def scorecard(rows: list[dict], name: str) -> dict:
    kinds = {"must_say": [0, 0], "must_not_say": [0, 0]}
    quality = defaultdict(lambda: [0, 0])
    fails = defaultdict(list)
    for r in rows:
        for v in r["verdicts"]:
            bucket = quality[v["id"]] if v["kind"] == "quality" else kinds[v["kind"]]
            bucket[1] += 1
            bucket[0] += v["verdict"] == "pass"
            if v["verdict"] == "fail":
                fails[r["week"]].append(v["id"])
    sw = [w for r in rows for w in r.get("so_whats", [])]
    per_week = {r["week"]: {"implication": sum(w["verdict"] == "implication" for w in r.get("so_whats", [])),
                            "total": len(r.get("so_whats", []))} for r in rows}
    return {
        "experiment": name, "judge": JUDGE_VERSION, "weeks": len(rows),
        "so_whats": {"implication": sum(w["verdict"] == "implication" for w in sw), "total": len(sw),
                     "by_week": per_week},
        "must_say": {"passed": kinds["must_say"][0], "total": kinds["must_say"][1]},
        "must_not_say": {"passed": kinds["must_not_say"][0], "total": kinds["must_not_say"][1]},
        "quality": {q: {"passed": quality[q][0], "total": quality[q][1]} for q in QUALITY_RULES},
        "fails_by_week": dict(fails),
        "judge_cost_usd": round(sum(r.get("cost_usd", 0) for r in rows), 3),
    }


def pct(p: dict) -> str:
    return f"{p['passed']} of {p['total']} ({100 * p['passed'] / p['total']:.0f}%)" if p["total"] else "n/a"


def to_markdown(s: dict) -> str:
    lines = [f"# Quality scorecard: {s['experiment']} (judged by {s['judge']})", "",
             "| Measure | Result |", "|---|---|",
             f"| Must-say items conveyed | {pct(s['must_say'])} |",
             f"| Must-not-say items avoided | {pct(s['must_not_say'])} |",
             f"| So-whats that are real implications | {pct({'passed': s['so_whats']['implication'], 'total': s['so_whats']['total']})} |"]
    lines += [f"| Quality: {q.replace('_', ' ')} | {pct(v)} weeks |" for q, v in s["quality"].items()]
    lines += [f"| Judge cost | ${s['judge_cost_usd']} |", "", "## Failures by week", "", "| Week | Failed items |", "|---|---|"]
    lines += [f"| {w} | {', '.join(ids)} |" for w, ids in sorted(s["fails_by_week"].items())]
    lines += ["", "## So-whats by week", "", "| Week | Implications | Share |", "|---|---|---|"]
    lines += [f"| {w} | {v['implication']} of {v['total']} | {100 * v['implication'] / v['total']:.0f}% |"
              for w, v in sorted(s["so_whats"]["by_week"].items()) if v["total"]]
    return "\n".join(lines) + "\n"


def calibration_sheet(rows: list[dict], name: str, n: int = 20) -> str:
    """A fixed random sample of verdicts for the human to label. Agreement = how far to trust the judge."""
    pool = [(r["week"], v) for r in rows for v in r["verdicts"]]
    pool += [(r["week"], {"id": f"so_what {w['slot']} {w['point']}", "kind": "so_what",
                          "verdict": "pass" if w["verdict"] == "implication" else "fail",
                          "evidence": "", "reason": w["reason"]}) for r in rows for w in r.get("so_whats", [])]
    fails = [p for p in pool if p[1]["verdict"] == "fail"]
    passes = [p for p in pool if p[1]["verdict"] == "pass"]
    rng = random.Random(42)
    sample = rng.sample(fails, min(len(fails), n // 2)) + rng.sample(passes, min(len(passes), n - min(len(fails), n // 2)))
    sample.sort(key=lambda p: (p[0], p[1]["kind"], p[1]["id"]))
    lines = [f"# Judge calibration: {name}", "",
             "For each row, read the evidence and write **pass** or **fail** in the 'Your verdict' column.",
             "Then we measure how often the judge agrees with you. Target: 85% or more before trusting it.", "",
             "| # | Week | Item | Kind | Judge | Evidence | Judge's reason | Your verdict |", "|---|---|---|---|---|---|---|---|"]
    for i, (w, v) in enumerate(sample, 1):
        ev = v["evidence"].replace("|", "/")[:160] or "(none)"
        lines.append(f"| {i} | {w} | {v['id']} | {v['kind']} | {v['verdict']} | {ev} | {v['reason'].replace('|', '/')} |  |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
