from datetime import date, datetime, timezone

from weekly_report.weeks import latest_completed_week, quarter_of, report_weeks, weeks_in_quarter


def test_latest_completed_week_never_returns_current_week():
    # Thursday 24 Sep 2026: current week started Mon 21 Sep, so report the week of 14 Sep
    assert latest_completed_week(datetime(2026, 9, 24, 19, 0, tzinfo=timezone.utc)) == date(2026, 9, 14)
    # Monday 8 AM ET (12:00 UTC) on 21 Sep: the week that just ended is 14 Sep
    assert latest_completed_week(datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)) == date(2026, 9, 14)


def test_mature_and_last_year_weeks():
    w = report_weeks(date(2026, 9, 14))
    assert w.prior == date(2026, 9, 7)
    assert w.mature == date(2026, 8, 31)
    assert w.last_year == date(2025, 9, 15)  # same Monday-to-Sunday week, 52 weeks back
    assert w.last_year.weekday() == 0


def test_quarter_uses_thursday_rule():
    assert quarter_of(date(2026, 6, 29)) == (2026, 3)   # Thursday is 2 Jul
    assert quarter_of(date(2026, 9, 28)) == (2026, 4)   # Thursday is 1 Oct
    q3 = weeks_in_quarter(2026, 3)
    assert q3[0] == date(2026, 6, 29) and q3[-1] == date(2026, 9, 21) and len(q3) == 13


def test_week_of_quarter_and_data_cutoff():
    w = report_weeks(date(2026, 9, 14))
    assert w.week_of_quarter == 12
    assert w.data_through.isoformat().startswith("2026-09-20T23:59:59")


def test_fiscal_year_and_month_assignment():
    from weekly_report.weeks import fiscal_year_weeks, month_of
    fy = fiscal_year_weeks(2026)
    assert fy[0] == date(2025, 12, 29) and fy[-1] == date(2026, 12, 28) and len(fy) == 53
    assert month_of(date(2026, 7, 27)) == (2026, 7)   # Thursday 30 Jul
    assert month_of(date(2026, 8, 3)) == (2026, 8)    # Thursday 6 Aug
