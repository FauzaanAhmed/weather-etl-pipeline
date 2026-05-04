from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from weather_etl.config import Settings, load_settings
from weather_etl.extract import combine_files, extract_archives
from weather_etl.load_db import connect, copy_batches, ensure_tmp_table, upsert_daily
from weather_etl.noaa_s3 import download_many, list_keys, list_recent_keys
from weather_etl.validate import validate_batch_files

logger = logging.getLogger(__name__)


def run_download(year: str, daily: bool = False, settings: Settings | None = None) -> list[str]:
    cfg = settings or load_settings()
    prefix = f"{cfg.noaa_prefix}/{year}/"
    keys = list_recent_keys(cfg.noaa_bucket, prefix) if daily else list_keys(cfg.noaa_bucket, prefix)
    raw_dir = Path(cfg.raw_dir)
    download_many(cfg.noaa_bucket, keys, raw_dir)
    return keys


def run_extract_and_batch(year: str, tag: str | None = None, settings: Settings | None = None) -> list[str]:
    cfg = settings or load_settings()
    raw_year = Path(cfg.raw_dir) / year
    clean_year = Path(cfg.clean_dir) / year
    extract_archives(raw_year)
    tag = tag or datetime.now(timezone.utc).strftime("%Y%m%d")
    batches = combine_files(raw_year, clean_year, cfg.batch_size, tag)
    return [str(p) for p in batches]


def run_validate(batch_paths: list[str]) -> dict:
    return validate_batch_files([Path(p) for p in batch_paths])


def run_load(batch_paths: list[str], settings: Settings | None = None) -> dict[str, int]:
    cfg = settings or load_settings()
    conn = connect(cfg)
    try:
        ensure_tmp_table(conn)
        copy_batches(conn, [Path(p) for p in batch_paths])
        upserted = upsert_daily(conn, cfg.min_hourly_records)
        return {"upserted_rows": upserted, "batch_count": len(batch_paths)}
    finally:
        conn.close()


def run_daily(year: str | None = None) -> dict:
    year = year or str(datetime.now(timezone.utc).year)
    cfg = load_settings()
    run_download(year, daily=True, settings=cfg)
    batches = run_extract_and_batch(year, settings=cfg)
    metrics = run_validate(batches)
    load_metrics = run_load(batches, settings=cfg)
    return {**metrics, **load_metrics}
