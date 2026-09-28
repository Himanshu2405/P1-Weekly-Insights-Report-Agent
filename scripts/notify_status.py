"""Post one comment to the "Weekly Report Status" tracking issue after every SCHEDULED run
(success or failure). Never called for a manual workflow_dispatch run; the workflow gates that.

Watching that issue is what triggers an email: GitHub notifies subscribers on new comments,
so this reuses GitHub's own notification pipeline instead of a separate SMTP setup.
"""

import datetime
import json
import os
import subprocess
import sys

STATUS_ISSUE = 2
RUN_LOG = "runs/run_log.jsonl"
LIVE_URL = "https://himanshu2405.github.io/P1-Weekly-Insights-Report-Agent/"
FRESH_MINUTES = 30  # a log entry older than this predates the current run


def fresh_run_summary() -> str:
    try:
        last = json.loads(open(RUN_LOG).readlines()[-1])
        logged = datetime.datetime.fromisoformat(last["logged_at_utc"].replace("Z", "+00:00"))
        age_min = (datetime.datetime.now(datetime.timezone.utc) - logged).total_seconds() / 60
        if age_min > FRESH_MINUTES:
            raise ValueError("stale entry")
        return (f"Status: {last['status']}, attempts: {last['attempts']}, "
                f"checks: {last['checks_passed']}/{last['checks_total']}, "
                f"cost: ${last['llm_cost_usd']:.4f}")
    except Exception:
        return "No fresh run log entry (the run failed before the report step logged one)."


def main() -> None:
    job_status = os.environ.get("JOB_STATUS", "unknown")
    server_url = os.environ.get("GITHUB_SERVER_URL", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    today = datetime.date.today().isoformat()

    icon = "✅ succeeded" if job_status == "success" else "❌ failed"
    body = (
        f"{icon} — scheduled run, {today}\n\n"
        f"{fresh_run_summary()}\n\n"
        f"Report: {LIVE_URL}\n"
        f"Run: {server_url}/{repository}/actions/runs/{run_id}"
    )
    subprocess.run(
        ["gh", "issue", "comment", str(STATUS_ISSUE), "--repo", repository, "--body", body],
        check=True,
    )


if __name__ == "__main__":
    sys.exit(main())
