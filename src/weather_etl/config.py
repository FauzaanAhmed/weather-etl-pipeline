from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _settings_path() -> Path:
    override = os.getenv("SETTINGS_PATH")
    if override:
        return Path(override)
    return _root() / "config" / "settings.ini"


@dataclass(frozen=True)
class Settings:
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    raw_dir: str
    clean_dir: str
    noaa_bucket: str
    noaa_prefix: str
    batch_size: int
    min_hourly_records: int


def load_settings() -> Settings:
    path = _settings_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Copy config/settings.example.ini to config/settings.ini."
        )

    parser = configparser.ConfigParser()
    parser.read(path)

    return Settings(
        postgres_host=parser.get("postgres", "host", fallback="postgres"),
        postgres_port=parser.getint("postgres", "port", fallback=5432),
        postgres_user=parser.get("postgres", "user", fallback="airflow"),
        postgres_password=parser.get("postgres", "password", fallback="airflow"),
        postgres_db=parser.get("postgres", "database", fallback="airflow"),
        raw_dir=parser.get("paths", "raw_dir", fallback="/opt/airflow/data/raw"),
        clean_dir=parser.get("paths", "clean_dir", fallback="/opt/airflow/data/clean"),
        noaa_bucket=parser.get("noaa", "bucket", fallback="noaa-isd-pds"),
        noaa_prefix=parser.get("noaa", "prefix", fallback="isd-lite/data"),
        batch_size=parser.getint("pipeline", "batch_size", fallback=500),
        min_hourly_records=parser.getint("pipeline", "min_hourly_records", fallback=4),
    )


ISD_LITE_COLUMNS = (
    "station_id",
    "year",
    "month",
    "day",
    "hour",
    "air_temperature",
    "dew_point",
    "sea_lvl_pressure",
    "wind_direction",
    "wind_speed",
    "sky_condition",
    "one_hour_precipitation",
    "six_hour_precipitation",
)
