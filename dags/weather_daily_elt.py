"""Daily NOAA ISD ELT — download, extract, validate, load, upsert."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from weather_etl.pipeline import run_daily, run_download, run_extract_and_batch, run_load, run_validate

default_args = {
    "owner": "fauzaan",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=8),
}


def _year(**context) -> str:
    return context["data_interval_start"].strftime("%Y")


def download_task(**context) -> None:
    year = _year(**context)
    run_download(year, daily=True)


def extract_task(**context) -> list[str]:
    year = _year(**context)
    tag = context["data_interval_start"].strftime("%Y%m%d")
    return run_extract_and_batch(year, tag=tag)


def validate_task(**context) -> dict:
    ti = context["ti"]
    batches = ti.xcom_pull(task_ids="extract_batch")
    return run_validate(batches)


def load_task(**context) -> dict:
    ti = context["ti"]
    batches = ti.xcom_pull(task_ids="extract_batch")
    return run_load(batches)


with DAG(
    dag_id="weather_daily_elt",
    description="Daily NOAA ISD ingest into Postgres",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="1 0 * * *",
    catchup=False,
    tags=["weather", "noaa", "elt"],
) as dag:
    download = PythonOperator(task_id="download_noaa", python_callable=download_task)
    extract = PythonOperator(task_id="extract_batch", python_callable=extract_task)
    validate = PythonOperator(task_id="validate_batches", python_callable=validate_task)
    load = PythonOperator(task_id="load_and_upsert", python_callable=load_task)

    download >> extract >> validate >> load
