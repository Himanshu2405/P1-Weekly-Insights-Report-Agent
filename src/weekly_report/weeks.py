"""Calendar logic: which week to report, which week is mature, which quarter a week belongs to.

All weeks are Monday to Sunday in UTC and are identified by their Monday (week_start).
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from . import config


def week_start(d: date) -> date:
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def latest_completed_week(now: datetime) -> date:
    """Monday of the most recent fully finished week. Never the in-progress week."""
    return week_start(now.astimezone(timezone.utc).date()) - timedelta(weeks=1)


def mature_week(reporting_week: date) -> date:
    """Week used for the 14-Day Return Rate: every order in it has had the full return window."""
    return reporting_week - timedelta(weeks=config.MATURITY_LAG_WEEKS)


def same_week_last_year(week: date) -> date:
    return week - timedelta(days=config.YOY_OFFSET_DAYS)


def quarter_of(week: date) -> tuple[int, int]:
    """(year, quarter) of a week, using the week's Thursday (same convention as ISO weeks).

    A week that spans two quarters belongs to the quarter holding most of its days.
    """
    thursday = week + timedelta(days=3)
    return thursday.year, (thursday.month - 1) // 3 + 1


def month_of(week: date) -> tuple[int, int]:
    """(year, month) of a week, by its Thursday (same rule as quarters)."""
    thursday = week + timedelta(days=3)
    return thursday.year, thursday.month


def fiscal_year_weeks(year: int) -> list[date]:
    """All weeks of a Jan-to-Dec fiscal year (weeks whose Thursday falls in that year)."""
    w = week_start(date(year, 1, 1)) - timedelta(weeks=1)
    out = []
    while True:
        if quarter_of(w)[0] == year:
            out.append(w)
        elif out:
            return out
        w += timedelta(weeks=1)


def weeks_in_quarter(year: int, quarter: int) -> list[date]:
    """All week_starts whose Thursday falls in the given quarter, in order."""
    first_day = date(year, 3 * (quarter - 1) + 1, 1)
    w = week_start(first_day) - timedelta(weeks=1)
    out = []
    while True:
        if quarter_of(w) == (year, quarter):
            out.append(w)
        elif out:
            return out
        w += timedelta(weeks=1)


@dataclass(frozen=True)
class ReportWeeks:
    reporting: date
    prior: date
    last_year: date
    mature: date
    mature_prior: date
    mature_last_year: date
    quarter: tuple[int, int]
    quarter_weeks: list[date]
    fy_weeks: list[date]

    @property
    def week_of_quarter(self) -> int:
        return self.quarter_weeks.index(self.reporting) + 1

    @property
    def data_through(self) -> datetime:
        """Last instant of the reporting week. Events after this are ignored."""
        return datetime.combine(self.reporting + timedelta(days=7), datetime.min.time(), timezone.utc) - timedelta(microseconds=1)


def report_weeks(reporting: date) -> ReportWeeks:
    mature = mature_week(reporting)
    q = quarter_of(reporting)
    return ReportWeeks(
        reporting=reporting,
        prior=reporting - timedelta(weeks=1),
        last_year=same_week_last_year(reporting),
        mature=mature,
        mature_prior=mature - timedelta(weeks=1),
        mature_last_year=same_week_last_year(mature),
        quarter=q,
        quarter_weeks=weeks_in_quarter(*q),
        fy_weeks=fiscal_year_weeks(q[0]),
    )
