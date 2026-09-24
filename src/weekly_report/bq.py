"""Thin BigQuery wrapper: named SQL files, typed parameters, a bytes-billed cap, and a scan log."""

import warnings
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd
from google.cloud import bigquery

from . import config

warnings.filterwarnings("ignore", message=".*BigQuery Storage module not found.*")


def _param(name: str, value) -> bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter:
    if isinstance(value, list):
        kind = "DATE" if value and isinstance(value[0], date) else "STRING"
        return bigquery.ArrayQueryParameter(name, kind, value)
    if isinstance(value, datetime):
        return bigquery.ScalarQueryParameter(name, "TIMESTAMP", value)
    if isinstance(value, date):
        return bigquery.ScalarQueryParameter(name, "DATE", value)
    raise TypeError(f"Unsupported query parameter type for {name}: {type(value)}")


@dataclass
class BigQueryRunner:
    client: bigquery.Client = field(default_factory=lambda: bigquery.Client(project=config.GCP_PROJECT))
    bytes_billed: int = 0
    cache_hits: int = 0
    queries: int = 0

    def run(self, sql_name: str, **params) -> pd.DataFrame:
        sql = (config.SQL_DIR / f"{sql_name}.sql").read_text()
        job_config = bigquery.QueryJobConfig(
            query_parameters=[_param(k, v) for k, v in params.items()],
            maximum_bytes_billed=config.MAX_BYTES_BILLED,
        )
        job = self.client.query(sql, job_config=job_config)
        df = job.to_dataframe()
        self.bytes_billed += job.total_bytes_billed or 0
        self.cache_hits += bool(job.cache_hit)
        self.queries += 1
        return df
