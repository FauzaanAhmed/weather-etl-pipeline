from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WeatherQualityError(Exception):
    pass


def validate_batch_files(batch_files: list[Path], min_files: int = 1) -> dict[str, int | float]:
    if len(batch_files) < min_files:
        raise WeatherQualityError(f"Expected at least {min_files} batch files, got {len(batch_files)}")

    total_lines = 0
    for path in batch_files:
        if not path.exists() or path.stat().st_size == 0:
            raise WeatherQualityError(f"Empty or missing batch file: {path}")
        total_lines += sum(1 for _ in path.open(encoding="utf-8"))

    if total_lines == 0:
        raise WeatherQualityError("No weather records found in batch files")

    metrics = {"batch_count": len(batch_files), "row_count": total_lines}
    logger.info("batch checks ok: %s", metrics)
    return metrics
