"""Pure functions for changes, polarity, and flag rules. No I/O, so they are easy to unit test."""

from typing import Literal, Sequence

from . import config

ChangeUnit = Literal["pct", "pp"]
Assessment = Literal["good", "bad", "flat"]
Direction = Literal["up", "down", "flat"]


def change(value: float, base: float | None, unit: ChangeUnit) -> float | None:
    """WoW or YoY change. pct = relative %, pp = percentage-point difference. Rounded to 1 decimal."""
    if base is None or value is None:
        return None
    if unit == "pp":
        return round(value - base, 1)
    if base == 0:
        return None
    return round((value / base - 1) * 100, 1)


def direction(delta: float | None) -> Direction:
    if delta is None or delta == 0:
        return "flat"
    return "up" if delta > 0 else "down"


def assessment(delta: float | None, higher_is_good: bool) -> Assessment:
    """Is this change good or bad for the business? Decided by code, never by the LLM."""
    if delta is None or delta == 0:
        return "flat"
    return "good" if (delta > 0) == higher_is_good else "bad"


def is_notable(value: float, wow: float | None, unit: ChangeUnit, previous_8: Sequence[float]) -> tuple[bool, str | None]:
    """Notable = big WoW move, or value outside its recent range."""
    if wow is not None:
        if unit == "pct" and abs(wow) >= config.NOTABLE_PCT:
            return True, f"WoW change of {wow:+.1f}% is at or above the {config.NOTABLE_PCT:.0f}% threshold"
        if unit == "pp" and abs(wow) >= config.NOTABLE_PP:
            return True, f"WoW change of {wow:+.1f} pp is at or above the {config.NOTABLE_PP:.1f} pp threshold"
    if previous_8 and (value > max(previous_8) or value < min(previous_8)):
        return True, "value is outside its 8-week range"
    return False, None


def anomaly_ratio(value: float, previous_8: Sequence[float]) -> float | None:
    """Returns value / 8-week average when it breaches the anomaly thresholds, else None."""
    if not previous_8:
        return None
    avg = sum(previous_8) / len(previous_8)
    if avg == 0:
        return None
    ratio = value / avg
    if ratio > config.ANOMALY_HIGH_RATIO or ratio < config.ANOMALY_LOW_RATIO:
        return round(ratio, 1)
    return None


def bad_streak(series: Sequence[float], higher_is_good: bool) -> int:
    """Number of consecutive weekly moves in the bad direction, ending at the last value."""
    count = 0
    for prev, cur in zip(reversed(series[:-1]), reversed(series[1:])):
        moved_bad = cur < prev if higher_is_good else cur > prev
        if not moved_bad:
            break
        count += 1
    return count
