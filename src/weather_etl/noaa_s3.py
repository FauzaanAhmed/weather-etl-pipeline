from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def _client():
    return boto3.client("s3", config=Config(signature_version=UNSIGNED, max_pool_connections=50))


def list_keys(bucket: str, prefix: str) -> list[str]:
    client = _client()
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    logger.info("Found %s objects under s3://%s/%s", len(keys), bucket, prefix)
    return keys


def list_recent_keys(bucket: str, prefix: str, hours: int = 24) -> list[str]:
    client = _client()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] >= cutoff:
                keys.append(obj["Key"])
    logger.info("Found %s objects modified in last %sh under %s", len(keys), hours, prefix)
    return keys


def download_key(bucket: str, key: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        _client().download_file(bucket, key, str(dest))
    except ClientError as exc:
        logger.error("Failed to download %s: %s", key, exc)
        raise
    return dest


def download_many(bucket: str, keys: list[str], raw_dir: Path, max_workers: int = 8) -> list[Path]:
    def _one(key: str) -> Path:
        year = key.split("/")[2]
        filename = key.split("/")[-1]
        return download_key(bucket, key, raw_dir / year / filename)

    paths: list[Path] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for path in pool.map(_one, keys):
            paths.append(path)
    logger.info("Downloaded %s files to %s", len(paths), raw_dir)
    return paths
