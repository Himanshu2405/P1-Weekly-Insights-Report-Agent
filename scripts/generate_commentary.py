"""AI commentary only (no BigQuery, no page): load a saved brief, run generate -> guards -> retry -> fallback.

Usage:
    python scripts/generate_commentary.py                          # config.AS_OF_WEEK
    python scripts/generate_commentary.py --week 2026-07-06 --version v1 --no-cache
"""

import argparse
import sys
from datetime import date

from weekly_report import config
from weekly_report.commentary import produce
from weekly_report.models import DataBrief


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week", type=date.fromisoformat, default=config.AS_OF_WEEK)
    parser.add_argument("--version", default=config.PROMPT_VERSION)
    parser.add_argument("--model", default=config.LLM_MODEL)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    brief = DataBrief.model_validate_json((config.BRIEFS_DIR / f"brief_{args.week.isoformat()}.json").read_text())
    o = produce(brief, version=args.version, model=args.model, use_cache=not args.no_cache)
    print(f"Week {args.week} | {o.status} | prompt {o.prompt_version} | {o.model} | attempts {len(o.attempts)} | "
          f"${o.cost_usd:.4f} | {o.duration_ms / 1000:.1f} s{' | cached' if o.cache_hit else ''}")
    for c in (o.guard_report or {}).get("checks", []):
        print(f"  [{'x' if c['passed'] else ' '}] {c['name']} ({c['severity']})")
        for d in c["details"][:4]:
            print(f"      - {d}")
    return 0 if o.status != "fallback" else 2


if __name__ == "__main__":
    sys.exit(main())
