"""Exit 0 if it's currently the scheduled run hour (8am America/New_York), else exit 1.

Called by the weekly GitHub Actions workflow, which fires two cron triggers (12:00 and
13:00 UTC Monday) because GitHub Actions cron has no daylight-saving support. Only one
of the two should actually build and publish the report; see weekly_report.schedule.
"""

import sys
from datetime import datetime, timezone

from weekly_report.schedule import is_scheduled_run

if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    if is_scheduled_run(now):
        print(f"{now.isoformat()}: scheduled hour (8am ET), proceeding")
        sys.exit(0)
    print(f"{now.isoformat()}: not the scheduled hour, skipping this trigger")
    sys.exit(1)
