from __future__ import annotations

import gzip
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_archives(raw_year_dir: Path) -> list[Path]:
    """Gunzip noaa .gz files and return paths to extracted text files."""
    raw_year_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    for gz_path in raw_year_dir.glob("*.gz"):
        if gz_path.stat().st_size == 0:
            logger.warning("Skipping empty archive %s", gz_path.name)
            gz_path.unlink(missing_ok=True)
            continue
        out_path = gz_path.with_suffix("")
        with gzip.open(gz_path, "rb") as src, open(out_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
        extracted.append(out_path)
        gz_path.unlink(missing_ok=True)
    logger.info("Extracted %s archives in %s", len(extracted), raw_year_dir)
    return extracted


def prefix_station_id(file_path: Path) -> None:
    """ISD-lite rows omit station id — derive it from the filename (USAF-WBAN)."""
    parts = file_path.stem.split("-")
    station_id = "-".join(parts[:2]) if len(parts) >= 3 else file_path.stem
    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    prefixed = []
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        prefixed.append(f"{station_id} {' '.join(parts)}")
    file_path.write_text("\n".join(prefixed) + "\n", encoding="utf-8")


def combine_files(raw_year_dir: Path, clean_year_dir: Path, batch_size: int, tag: str) -> list[Path]:
    """Merge station files into larger batches for faster COPY."""
    clean_year_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in raw_year_dir.iterdir() if p.is_file() and p.suffix == "")
    batches: list[Path] = []

    for i in range(0, len(files), batch_size):
        chunk = files[i : i + batch_size]
        batch_path = clean_year_dir / f"{tag}_batch_{i // batch_size:04d}.txt"
        with open(batch_path, "w", encoding="utf-8") as out:
            for fp in chunk:
                prefix_station_id(fp)
                out.write(fp.read_text(encoding="utf-8"))
        batches.append(batch_path)
        fp.unlink(missing_ok=True)

    logger.info("Built %s batch files in %s", len(batches), clean_year_dir)
    return batches
