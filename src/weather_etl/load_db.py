from __future__ import annotations

import logging
from pathlib import Path

import psycopg2
from psycopg2.extensions import connection

from weather_etl.config import ISD_LITE_COLUMNS, Settings

logger = logging.getLogger(__name__)

TMP_TABLE = "tmp_weather_staging"


def connect(settings: Settings) -> connection:
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        dbname=settings.postgres_db,
    )


def ensure_tmp_table(conn: connection) -> None:
    with conn, conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {TMP_TABLE};")
        cur.execute(
            f"""
            CREATE TABLE {TMP_TABLE} (
                station_id varchar(20) not null,
                year integer,
                month integer,
                day integer,
                hour integer,
                air_temperature integer,
                dew_point integer,
                sea_lvl_pressure integer,
                wind_direction integer,
                wind_speed integer,
                sky_condition integer,
                one_hour_precipitation integer,
                six_hour_precipitation integer
            );
            """
        )
    logger.info("Created staging table %s", TMP_TABLE)


def copy_batches(conn: connection, batch_files: list[Path]) -> int:
    copied = 0
    with conn.cursor() as cur:
        for path in batch_files:
            with path.open(encoding="utf-8") as fh:
                cur.copy_from(fh, TMP_TABLE, sep=" ", null="-9999")
            copied += 1
        conn.commit()
    logger.info("Copied %s batch files into %s", copied, TMP_TABLE)
    return copied


def upsert_daily(conn: connection, min_hourly_records: int) -> int:
    sql = f"""
    INSERT INTO weather (
        station_id, date, n_records,
        air_temperature_avg, air_temperature_min, air_temperature_max,
        dew_point_avg, dew_point_min, dew_point_max,
        sea_lvl_pressure_avg, sea_lvl_pressure_min, sea_lvl_pressure_max,
        wind_direction, wind_speed_avg, wind_speed_min, wind_speed_max,
        sky_condition,
        one_hour_precipitation_avg, one_hour_precipitation_min, one_hour_precipitation_max,
        six_hour_precipitation_avg, six_hour_precipitation_min, six_hour_precipitation_max
    )
    SELECT
        station_id,
        make_date(year, month, day) AS date,
        count(hour) AS n_records,
        avg(air_temperature), min(air_temperature), max(air_temperature),
        avg(dew_point), min(dew_point), max(dew_point),
        avg(sea_lvl_pressure), min(sea_lvl_pressure), max(sea_lvl_pressure),
        avg(wind_direction),
        avg(wind_speed), min(wind_speed), max(wind_speed),
        round(avg(sky_condition))::int,
        avg(one_hour_precipitation), min(one_hour_precipitation), max(one_hour_precipitation),
        avg(six_hour_precipitation), min(six_hour_precipitation), max(six_hour_precipitation)
    FROM {TMP_TABLE}
    GROUP BY station_id, make_date(year, month, day)
    HAVING count(hour) >= %s
    ON CONFLICT (station_id, date) DO UPDATE SET
        n_records = EXCLUDED.n_records,
        air_temperature_avg = EXCLUDED.air_temperature_avg,
        air_temperature_min = EXCLUDED.air_temperature_min,
        air_temperature_max = EXCLUDED.air_temperature_max,
        dew_point_avg = EXCLUDED.dew_point_avg,
        dew_point_min = EXCLUDED.dew_point_min,
        dew_point_max = EXCLUDED.dew_point_max,
        sea_lvl_pressure_avg = EXCLUDED.sea_lvl_pressure_avg,
        sea_lvl_pressure_min = EXCLUDED.sea_lvl_pressure_min,
        sea_lvl_pressure_max = EXCLUDED.sea_lvl_pressure_max,
        wind_direction = EXCLUDED.wind_direction,
        wind_speed_avg = EXCLUDED.wind_speed_avg,
        wind_speed_min = EXCLUDED.wind_speed_min,
        wind_speed_max = EXCLUDED.wind_speed_max,
        sky_condition = EXCLUDED.sky_condition,
        one_hour_precipitation_avg = EXCLUDED.one_hour_precipitation_avg,
        one_hour_precipitation_min = EXCLUDED.one_hour_precipitation_min,
        one_hour_precipitation_max = EXCLUDED.one_hour_precipitation_max,
        six_hour_precipitation_avg = EXCLUDED.six_hour_precipitation_avg,
        six_hour_precipitation_min = EXCLUDED.six_hour_precipitation_min,
        six_hour_precipitation_max = EXCLUDED.six_hour_precipitation_max;
    """
    with conn, conn.cursor() as cur:
        cur.execute(sql, (min_hourly_records,))
        rows = cur.rowcount
    with conn, conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {TMP_TABLE};")
    logger.info("Upserted %s daily rows station rows", rows)
    return rows
