"""Scheduling guard for the weekly GitHub Actions run.

GitHub Actions cron is UTC only, with no daylight-saving support, so the workflow fires
two triggers on Monday (12:00 and 13:00 UTC) to bracket 8am America/New_York across both
EST and EDT. Only the trigger that actually lands on 8am ET should build and publish;
the other is a no-op.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

TARGET_HOUR_ET = 8


def is_scheduled_run(now: datetime) -> bool:
    """True if `now` falls in the 8am America/New_York hour, the intended run time."""
    et = now.astimezone(ZoneInfo("America/New_York"))
    return et.hour == TARGET_HOUR_ET
