"""Clean the latest Open-Meteo weather forecast snapshot."""

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


WEATHER_COLUMNS = [
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "weather_code",
    "wind_speed_10m",
    "wind_gusts_10m",
]

WMO_WEATHER_LABELS = {
    0: "clear_sky",
    1: "mainly_clear",
    2: "partly_cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing_rime_fog",
    51: "light_drizzle",
    53: "moderate_drizzle",
    55: "dense_drizzle",
    56: "light_freezing_drizzle",
    57: "dense_freezing_drizzle",
    61: "slight_rain",
    63: "moderate_rain",
    65: "heavy_rain",
    66: "light_freezing_rain",
    67: "heavy_freezing_rain",
    71: "slight_snowfall",
    73: "moderate_snowfall",
    75: "heavy_snowfall",
    77: "snow_grains",
    80: "slight_rain_showers",
    81: "moderate_rain_showers",
    82: "violent_rain_showers",
    85: "slight_snow_showers",
    86: "heavy_snow_showers",
    95: "thunderstorm",
    96: "thunderstorm_slight_hail",
    99: "thunderstorm_heavy_hail",
}


def wrangle_weather(source: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    raw = load_hourly_snapshot(source)
    require_columns(raw, WEATHER_COLUMNS)
    clean = add_time_columns(raw)

    for column in WEATHER_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="raise")
    clean["weather_code"] = clean["weather_code"].astype("int16")
    clean["weather_description"] = clean["weather_code"].map(WMO_WEATHER_LABELS)
    if clean["weather_description"].isna().any():
        unknown = sorted(clean.loc[clean["weather_description"].isna(), "weather_code"].unique())
        raise ValueError(f"Unmapped WMO weather codes: {unknown}")

    require_unique_site_time(clean)
    require_range(clean, "temperature_2m", -60, 60)
    require_range(clean, "apparent_temperature", -80, 70)
    require_range(clean, "precipitation_probability", 0, 100)
    require_range(clean, "wind_speed_10m", 0, 300)
    require_range(clean, "wind_gusts_10m", 0, 400)

    clean = clean.sort_values(["site_name", "timestamp_local"]).reset_index(drop=True)
    report = base_report(source, raw, clean)
    report["weather_code_mapping_complete"] = True
    report["range_checks_passed"] = True
    return clean, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument(
        "--output", type=Path, default=PROCESSED_DIR / "weather_forecast_clean.csv"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=VALIDATION_DIR / "weather_forecast_wrangling_report.json",
    )
    args = parser.parse_args()

    source = latest_snapshot(args.raw_dir, "weather_forecast")
    clean, report = wrangle_weather(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    write_report(args.report, report)
    print(f"Wrote {len(clean):,} rows to {args.output}")
    print(f"Wrote validation report to {args.report}")


if __name__ == "__main__":
    main()
