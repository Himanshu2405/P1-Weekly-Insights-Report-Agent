"""Project-wide settings. Tunable rule thresholds live here, not scattered in code."""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = Path(__file__).resolve().parent / "sql"
TARGETS_FILE = ROOT / "targets" / "weekly_targets_2026.csv"
BRIEFS_DIR = ROOT / "briefs"
LAYOUT_FILE = ROOT / "report_layout.yaml"

# BigQuery
GCP_PROJECT = "master-chariot-413216"
SOURCE_DATASET = "bigquery-public-data.thelook_ecommerce"
MAX_BYTES_BILLED = 500 * 1024**2  # hard stop: any single query scanning > 500 MB fails

# Plan (targets)
TARGET_VERSION = "plan_2026_v1"
PLAN_YEAR = 2026
PLAN_GROWTH_PCT = 75.0

# Reporting clock. The public dataset has a data break from the week of 2026-09-14 (signups 6x,
# orders 1.7x their 8-week average) and accelerating growth from 2026-08-10. The report is frozen
# at the last week of steady data. Set to None to report the latest completed week instead.
AS_OF_WEEK = date(2026, 8, 3)
FISCAL_YEAR = 2026            # fiscal year = calendar year (Jan to Dec)
ARCHIVE_WEEKS = 8             # past reports backfilled for the archive

# Time windows
HISTORY_WEEKS = 52          # trend charts
LOOKBACK_WEEKS = 120        # SQL pulls enough weeks for history + same week last year
RETURN_WINDOW_DAYS = 14
MATURITY_LAG_WEEKS = 2      # 14-Day Return Rate is reported for the week 2 weeks before the reporting week
YOY_OFFSET_DAYS = 364       # same Monday-to-Sunday week last year (52 weeks back)

# Rules for notable changes and flags
NOTABLE_PCT = 10.0          # |WoW| >= 10% for counts and money
NOTABLE_PP = 1.0            # |WoW| >= 1.0 pp for rates
ANOMALY_HIGH_RATIO = 2.0    # value > 2x its 8-week average
ANOMALY_LOW_RATIO = 0.5     # value < 0.5x its 8-week average
STREAK_WEEKS = 3            # 3+ consecutive moves in the bad direction

# Region mapping. Any country not listed here fails the data-quality gate.
REGION_BY_COUNTRY = {
    "China": "APAC", "South Korea": "APAC", "Japan": "APAC", "Australia": "APAC",
    "United States": "North America",
    "France": "EMEA", "United Kingdom": "EMEA", "Germany": "EMEA", "Spain": "EMEA",
    "Belgium": "EMEA", "Poland": "EMEA", "Austria": "EMEA",
    "España": "EMEA", "Deutschland": "EMEA",
    "Brasil": "LATAM", "Colombia": "LATAM",
}
REGIONS = ["APAC", "North America", "EMEA", "LATAM"]
TRAFFIC_SOURCES = ["Search", "Organic", "Facebook", "Email", "Display"]
