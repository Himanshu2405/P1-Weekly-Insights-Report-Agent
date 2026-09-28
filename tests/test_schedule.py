"""The double cron trigger (12:00 and 13:00 UTC) must resolve to exactly one real run."""

from datetime import datetime, timezone

from weekly_report.schedule import is_scheduled_run


def test_13_00_utc_is_8am_et_in_standard_time():
    assert is_scheduled_run(datetime(2026, 1, 5, 13, 0, tzinfo=timezone.utc))


def test_12_00_utc_is_not_8am_et_in_standard_time():
    assert not is_scheduled_run(datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc))


def test_12_00_utc_is_8am_et_in_daylight_time():
    assert is_scheduled_run(datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc))


def test_13_00_utc_is_not_8am_et_in_daylight_time():
    assert not is_scheduled_run(datetime(2026, 9, 7, 13, 0, tzinfo=timezone.utc))


def test_manual_dispatch_mid_afternoon_is_not_scheduled_hour():
    assert not is_scheduled_run(datetime(2026, 9, 7, 20, 0, tzinfo=timezone.utc))
