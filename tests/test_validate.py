from pathlib import Path

import pytest

from weather_etl.validate import WeatherQualityError, validate_batch_files


def test_validate_rejects_empty_batch_list(tmp_path: Path) -> None:
    with pytest.raises(WeatherQualityError):
        validate_batch_files([])


def test_validate_accepts_nonempty_batch(tmp_path: Path) -> None:
    batch = tmp_path / "batch.txt"
    batch.write_text("station 2024 1 1 0 10 5 1010 180 5 0 0 0\n", encoding="utf-8")
    metrics = validate_batch_files([batch])
    assert metrics["row_count"] == 1
    assert metrics["batch_count"] == 1
    assert metrics["total_bytes"] > 0
