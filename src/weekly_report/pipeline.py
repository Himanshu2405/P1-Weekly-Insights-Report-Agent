"""One run of the data side of the pipeline: query once, build everything downstream needs."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from . import config, targets
from .bq import BigQueryRunner
from .brief import add_kpis, assemble, map_regions, split_facts
from .models import DataBrief
from .weeks import ReportWeeks, report_weeks


@dataclass
class RunData:
    weeks: ReportWeeks
    kpis: pd.DataFrame        # one row per week, KPIs derived and rounded
    cuts: pd.DataFrame        # compared weeks x country x traffic source, with region
    plan: pd.DataFrame        # frozen weekly targets
    brief: DataBrief
    bytes_billed: int
    cache_hit: bool
    run_at: datetime


def collect(reporting: date, now: datetime | None = None) -> RunData:
    now = now or datetime.now(timezone.utc)
    weeks = report_weeks(reporting)
    runner = BigQueryRunner()
    facts = runner.run("weekly_facts", start_week=reporting - timedelta(weeks=config.LOOKBACK_WEEKS),
                       data_through=weeks.data_through)
    weekly, cuts = split_facts(facts, weeks)
    plan = targets.load()
    brief = assemble(weekly, cuts, plan, weeks, now=now)
    cuts_mapped, _ = map_regions(cuts)
    return RunData(weeks, add_kpis(weekly), cuts_mapped, plan, brief, runner.bytes_billed,
                   runner.cache_hits == runner.queries, now)


def save_brief(run: RunData) -> str:
    config.BRIEFS_DIR.mkdir(exist_ok=True)
    out = config.BRIEFS_DIR / f"brief_{run.weeks.reporting.isoformat()}.json"
    out.write_text(run.brief.model_dump_json(indent=2))
    return out.name
