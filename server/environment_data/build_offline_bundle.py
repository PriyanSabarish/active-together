"""CLI: download and build the three-LGA seven-day offline bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from .cache import CacheRepository
from .open_meteo_client import OpenMeteoClient
from .service import EnvironmentService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cache-dir", type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "environment_cache",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    service = EnvironmentService(
        OpenMeteoClient(timeout_seconds=args.timeout), CacheRepository(args.cache_dir)
    )
    count = service.refresh_offline_bundle()
    print(f"Wrote {count:,} hourly records for melton, melbourne and monash")
    print(service.repository.offline_path)


if __name__ == "__main__":
    main()
