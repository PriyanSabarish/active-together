"""Shared helpers for wrangling Open-Meteo multi-location JSON snapshots."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "open_meteo"
PROCESSED_DIR = REPO_ROOT / "data" / "processed" / "open_meteo"
VALIDATION_DIR = REPO_ROOT / "data" / "validation" / "open_meteo"


def latest_snapshot(raw_dir: Path, prefix: str) -> Path:
    candidates = sorted(raw_dir.glob(f"{prefix}_????-??-??.json"))
    if not candidates:
        raise FileNotFoundError(f"No {prefix} snapshot found in {raw_dir}")
    return candidates[-1]


def load_hourly_snapshot(path: Path) -> pd.DataFrame:
    """Flatten one multi-location API response and retain source metadata."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Expected a non-empty location list in {path}")

    frames: list[pd.DataFrame] = []
    for location in payload:
        hourly = pd.DataFrame(location["hourly"])
        metadata = {
            "site_name": location["site_name"],
            "requested_latitude": location["requested_latitude"],
            "requested_longitude": location["requested_longitude"],
            "grid_latitude": location["latitude"],
            "grid_longitude": location["longitude"],
            "grid_elevation_m": location.get("elevation"),
            "source_timezone": location["timezone"],
            "source_file": path.name,
        }
        for position, (column, value) in enumerate(metadata.items()):
            hourly.insert(position, column, value)
        frames.append(hourly)
    return pd.concat(frames, ignore_index=True)


def add_time_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Parse API local time and add explicit local and UTC timestamps."""
    result = data.copy()
    parsed = pd.to_datetime(result.pop("time"), errors="raise")
    local = parsed.dt.tz_localize(
        "Australia/Sydney", ambiguous="raise", nonexistent="raise"
    )
    result.insert(8, "timestamp_local", local)
    result.insert(9, "timestamp_utc", local.dt.tz_convert("UTC"))
    result.insert(10, "date_local", local.dt.date.astype("string"))
    result.insert(11, "hour_local", local.dt.hour.astype("int8"))
    return result


def require_columns(data: pd.DataFrame, required: list[str]) -> None:
    missing = sorted(set(required).difference(data.columns))
    if missing:
        raise ValueError(f"Required columns missing: {missing}")


def require_unique_site_time(data: pd.DataFrame) -> None:
    duplicates = data.duplicated(["site_name", "timestamp_local"], keep=False)
    if duplicates.any():
        examples = data.loc[duplicates, ["site_name", "timestamp_local"]].head()
        raise ValueError(f"Duplicate site-time keys found:\n{examples}")


def require_range(data: pd.DataFrame, column: str, lower: float, upper: float) -> None:
    invalid = data[column].notna() & ~data[column].between(lower, upper)
    if invalid.any():
        values = data.loc[invalid, column].head().tolist()
        raise ValueError(f"{column} outside [{lower}, {upper}]: {values}")


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def base_report(source: Path, before: pd.DataFrame, after: pd.DataFrame) -> dict[str, object]:
    return {
        "source_file": source.name,
        "input_rows": len(before),
        "output_rows": len(after),
        "removed_rows": len(before) - len(after),
        "site_count": int(after["site_name"].nunique()),
        "duplicate_site_time_keys": int(
            after.duplicated(["site_name", "timestamp_local"]).sum()
        ),
        "output_missing_by_column": {
            column: int(count)
            for column, count in after.isna().sum().items()
            if count > 0
        },
        "rows_per_site": {
            site: int(count)
            for site, count in after.groupby("site_name", sort=True).size().items()
        },
    }
