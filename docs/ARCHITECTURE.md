# Architecture

NOAA ISD hourly files land in Postgres as daily station aggregates.

## Flow

```text
NOAA open S3 (noaa-isd-pds)
    → download (boto3, unsigned)
    → gunzip + batch text files
    → validate row counts
    → COPY staging table
    → upsert into weather
    → Metabase / SQL analytics
```

## DAGs

| DAG | Schedule | Purpose |
|---|---|---|
| `weather_daily_elt` | daily 00:01 | ingest files modified in last 24h |
| `weather_backfill_elt` | yearly | full-year historical load |

## Notes

- ISD-lite values use `-9999` as missing; Postgres COPY maps that to NULL.
- Daily upsert requires at least 4 hourly readings per station/day (configurable).
- LocalExecutor keeps the stack simple for a laptop demo; swap to Celery if you need scale.
