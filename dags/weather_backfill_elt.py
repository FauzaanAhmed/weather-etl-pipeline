"""Backfill NOAA ISD data for a full calendar year."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from weather_etl.pipeline import run_download, run_extract_and_batch, run_load, run_validate

default_args = {
    "owner": "fauzaan",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(hours=1),
}


def download_task(**context) -> None:
    year = context["data_interval_start"].strftime("%Y")
    run_download(year, daily=False)


def extract_task(**context) -> list[str]:
    year = context["data_interval_start"].strftime("%Y")
    return run_extract_and_batch(year, tag=year)


def validate_task(**context) -> dict:
    batches = context["ti"].xcom_pull(task_ids="extract_batch")
    return run_validate(batches)


def load_task(**context) -> dict:
    batches = context["ti"].xcom_pull(task_ids="extract_batch")
    return run_load(batches)


with DAG(
    dag_id="weather_backfill_elt",
    description="Historical NOAA ISD backfill by year",
    default_args=default_args,
    start_date=datetime(2018, 1, 1),
    schedule="@yearly",
    catchup=True,
    max_active_runs=1  # one year at a time,
    tags=["weather", "noaa", "backfill"],
) as dag:
    download = PythonOperator(task_id="download_noaa", python_callable=download_task)
    extract = PythonOperator(task_id="extract_batch", python_callable=extract_task)
    validate = PythonOperator(task_id="validate_batches", python_callable=validate_task)
    load = PythonOperator(task_id="load_and_upsert", python_callable=load_task)

    download >> extract >> validate >> load
