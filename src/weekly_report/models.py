"""Data brief schema (v1.0) as Pydantic models.

The brief is the contract between the data pipeline and the LLM. Validating it on write means a
malformed brief can never reach the prompt. `extra="forbid"` catches typos and stray fields.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

BRIEF_VERSION = "1.0"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReportingWeek(Strict):
    start: date
    end: date
    quarter: str
    week_of_quarter: int
    weeks_in_quarter: int


class MatureWeek(Strict):
    start: date
    end: date
    used_for: list[str]


class Meta(Strict):
    run_id: str
    generated_at_utc: datetime
    reporting_week: ReportingWeek
    mature_week: MatureWeek
    data_through_utc: datetime
    source: str
    target_version: str
    layout_version: str
    plan_growth_pct: float


class QualityCheck(Strict):
    name: str
    passed: bool
    detail: str


class DataQuality(Strict):
    all_passed: bool
    checks: list[QualityCheck]


Assessment = Literal["good", "bad", "flat"]
Direction = Literal["up", "down", "flat"]


class Kpi(Strict):
    name: str
    format: Literal["count", "usd", "usd_cents", "percent"]
    higher_is_good: bool
    change_unit: Literal["pct", "pp"]
    week_ref: Literal["reporting", "mature"]
    value: float
    prior_week: Optional[float]
    wow_change: Optional[float]
    wow_direction: Direction
    wow_assessment: Assessment
    last_year: Optional[float]
    yoy_change: Optional[float]
    yoy_direction: Direction
    yoy_assessment: Assessment
    avg_8wk: Optional[float] = None
    notable: bool
    notable_reason: Optional[str] = None


class Kpis(Strict):
    orders: Kpi
    revenue: Kpi
    aov: Kpi
    cancellation_rate: Kpi
    return_rate_14d: Kpi
    new_signups: Kpi


class WeeklyTarget(Strict):
    actual: float
    target: float
    attainment_pct: float
    gap: float
    status: Literal["ahead", "behind", "on_target"]
    next_week_target: Optional[float]


class QtdTarget(Strict):
    actual: float
    target_to_date: float
    attainment_pct: float
    gap: float
    status: Literal["ahead", "behind", "on_target"]
    full_quarter_plan: float
    remaining_to_full_quarter_plan: float
    weeks_left: int


class Targets(Strict):
    orders_vs_target: WeeklyTarget
    revenue_vs_target: WeeklyTarget
    qtd_revenue_vs_target: QtdTarget


class Segment(Strict):
    segment: str
    value: float
    prior_week: float
    wow_pct: Optional[float]
    last_year: float
    yoy_pct: Optional[float]
    share_pct: float
    contribution: float
    share_of_change_pct: Optional[float]


class CutMetrics(Strict):
    orders: list[Segment]


class Cuts(Strict):
    region: CutMetrics
    traffic_source: CutMetrics


class History(Strict):
    week_start: list[date]
    orders: list[float]
    cancellation_rate: list[float]
    return_rate_14d: list[Optional[float]]


class Flag(Strict):
    id: str
    type: Literal["anomaly", "streak", "plan_context", "maturity"]
    severity: Literal["serious", "warning"]
    kpi: str
    detected_by: Literal["code"] = "code"
    facts: dict


class TopContributor(Strict):
    segment: str
    contribution: float
    share_of_change_pct: Optional[float]


class SoWhatFacts(Strict):
    next_week_targets: dict[str, Optional[float]]
    full_quarter_plan: float
    quarter_remaining_to_plan: float
    qtd_attainment_excl_flagged_pct: Optional[float]
    revenue_per_pp_cancellation: float
    avg_8wk: dict[str, float]
    top_contributor: dict[str, TopContributor]
    yoy_vs_plan_growth: dict[str, Optional[float]]
    signups_vs_orders_growth: dict[str, Optional[float]]
    segments_all_growing: dict[str, bool]


class DataBrief(Strict):
    brief_version: Literal["1.0"] = BRIEF_VERSION
    meta: Meta
    data_quality: DataQuality
    kpis: Kpis
    targets: Targets
    cuts: Cuts
    history_8wk: History
    flags: list[Flag]
    so_what_facts: SoWhatFacts
