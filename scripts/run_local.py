#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from weather_etl.pipeline import run_daily


def main() -> None:
    parser = argparse.ArgumentParser(description="Run daily weather ELT locally")
    parser.add_argument("--year", default=str(datetime.now(timezone.utc).year))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(run_daily(args.year))


if __name__ == "__main__":
    main()
