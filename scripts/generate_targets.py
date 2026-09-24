"""One-time: build the frozen 2026 plan file. Refuses to overwrite unless --force is given."""

import argparse
import sys

from weekly_report import config, targets
from weekly_report.bq import BigQueryRunner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite an existing plan file")
    args = parser.parse_args()

    if config.TARGETS_FILE.exists() and not args.force:
        print(f"{config.TARGETS_FILE} already exists. Targets are frozen; use --force only to issue a new plan version.")
        return 1

    runner = BigQueryRunner()
    df = targets.generate(runner)
    config.TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.TARGETS_FILE, index=False)
    print(f"Wrote {len(df)} weekly targets to {config.TARGETS_FILE} ({runner.bytes_billed / 1e6:.0f} MB billed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
