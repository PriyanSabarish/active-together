"""Clean the latest Open-Meteo air-quality forecast snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from open_meteo_common import (
    PROCESSED_DIR,
    RAW_DIR,
    VALIDATION_DIR,
    add_time_columns,
    base_report,
    latest_snapshot,
    load_hourly_snapshot,
    require_columns,
    require_range,
    require_unique_site_time,
    write_report,
)


AIR_COLUMNS = ["uv_index", "pm2_5", "pm10"]


def wrangle_air_quality(source: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    raw = load_hourly_snapshot(source)
    require_columns(raw, AIR_COLUMNS)
    clean = add_time_columns(raw)
    for column in AIR_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")

    all_metrics_missing = clean[AIR_COLUMNS].isna().all(axis=1)
    partially_missing = clean[AIR_COLUMNS].isna().any(axis=1) & ~all_metrics_missing
    if partially_missing.any():
        raise ValueError(
            "Partially missing air-quality rows require an explicit field-level policy"
        )

    removed = clean.loc[all_metrics_missing, ["site_name", "timestamp_local"]].copy()
    clean = clean.loc[~all_metrics_missing].copy()
    require_unique_site_time(clean)
    require_range(clean, "uv_index", 0, 30)
    require_range(clean, "pm2_5", 0, 1000)
    require_range(clean, "pm10", 0, 2000)

    clean = clean.sort_values(["site_name", "timestamp_local"]).reset_index(drop=True)
    report = base_report(source, raw, clean)
    report["missing_policy"] = (
        "Drop rows where UV, PM2.5, and PM10 are all missing; do not impute raw forecasts."
    )
    report["removed_all_metric_missing_rows"] = len(removed)
    report["removed_rows_by_site"] = {
        site: int(count)
        for site, count in removed.groupby("site_name", sort=True).size().items()
    }
    report["removed_timestamps"] = sorted(
        removed["timestamp_local"].astype(str).unique().tolist()
    )
    report["range_checks_passed"] = True
    return clean, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument(
        "--output", type=Path, default=PROCESSED_DIR / "air_quality_clean.csv"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=VALIDATION_DIR / "air_quality_wrangling_report.json",
    )
    args = parser.parse_args()

    source = latest_snapshot(args.raw_dir, "air_quality")
    clean, report = wrangle_air_quality(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    write_report(args.report, report)
    print(f"Wrote {len(clean):,} rows to {args.output}")
    print(f"Wrote validation report to {args.report}")


if __name__ == "__main__":
    main()
