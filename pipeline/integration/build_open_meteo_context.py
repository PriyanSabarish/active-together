"""Build the product-facing hourly weather and air-quality context table."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEATHER = (
    REPO_ROOT / "data" / "processed" / "open_meteo" / "weather_forecast_clean.csv"
)
DEFAULT_AIR = (
    REPO_ROOT / "data" / "processed" / "open_meteo" / "air_quality_clean.csv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "data"
    / "processed"
    / "integrated"
    / "hourly_environment_context.csv"
)

JOIN_KEYS = ["site_name", "timestamp_utc"]


def require_unique(data: pd.DataFrame, dataset_name: str) -> None:
    duplicates = data.duplicated(JOIN_KEYS, keep=False)
    if duplicates.any():
        examples = data.loc[duplicates, JOIN_KEYS].head().to_dict("records")
        raise ValueError(f"Duplicate keys in {dataset_name}: {examples}")


def build_context(weather_path: Path, air_path: Path) -> pd.DataFrame:
    weather = pd.read_csv(weather_path, parse_dates=["timestamp_local", "timestamp_utc"])
    air = pd.read_csv(air_path, parse_dates=["timestamp_local", "timestamp_utc"])
    require_unique(weather, "weather")
    require_unique(air, "air quality")

    weather_product = weather[
        [
            "site_name",
            "display_name",
            "lga_code",
            "timestamp_local",
            "timestamp_utc",
            "requested_latitude",
            "requested_longitude",
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "weather_code",
            "weather_description",
            "wind_speed_10m",
            "wind_gusts_10m",
        ]
    ].rename(
        columns={
            "requested_latitude": "latitude",
            "requested_longitude": "longitude",
            "temperature_2m": "temperature_c",
            "apparent_temperature": "apparent_temperature_c",
            "precipitation_probability": "precipitation_probability_pct",
            "wind_speed_10m": "wind_speed_kmh",
            "wind_gusts_10m": "wind_gusts_kmh",
        }
    )
    air_product = air[
        ["site_name", "timestamp_utc", "uv_index", "pm2_5", "pm10"]
    ].rename(columns={"pm2_5": "pm2_5_ugm3", "pm10": "pm10_ugm3"})

    context = weather_product.merge(
        air_product,
        on=JOIN_KEYS,
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    context["air_quality_available"] = context.pop("_merge").eq("both")
    context = context[
        [
            "site_name",
            "display_name",
            "lga_code",
            "timestamp_local",
            "timestamp_utc",
            "latitude",
            "longitude",
            "temperature_c",
            "apparent_temperature_c",
            "precipitation_probability_pct",
            "weather_code",
            "weather_description",
            "wind_speed_kmh",
            "wind_gusts_kmh",
            "uv_index",
            "pm2_5_ugm3",
            "pm10_ugm3",
            "air_quality_available",
        ]
    ].sort_values(["site_name", "timestamp_utc"], ignore_index=True)

    if len(context) != len(weather):
        raise AssertionError("The left join changed the number of weather rows")
    air_fields = ["uv_index", "pm2_5_ugm3", "pm10_ugm3"]
    availability_matches_values = context[air_fields].notna().all(axis=1).eq(
        context["air_quality_available"]
    )
    if not availability_matches_values.all():
        raise AssertionError("air_quality_available does not match air-quality values")
    if context.duplicated(JOIN_KEYS).any():
        raise AssertionError("Integrated output contains duplicate keys")
    return context


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weather", type=Path, default=DEFAULT_WEATHER)
    parser.add_argument("--air-quality", type=Path, default=DEFAULT_AIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    context = build_context(args.weather, args.air_quality)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = context.copy()
    serialized["timestamp_local"] = serialized["timestamp_local"].map(
        lambda value: value.isoformat()
    )
    serialized["timestamp_utc"] = serialized["timestamp_utc"].map(
        lambda value: value.isoformat()
    )
    serialized["air_quality_available"] = serialized[
        "air_quality_available"
    ].map({True: "true", False: "false"})
    serialized.to_csv(args.output, index=False)

    available = int(context["air_quality_available"].sum())
    unavailable = len(context) - available
    print(f"Wrote {len(context):,} rows to {args.output}")
    print(f"Air quality available: {available:,}; unavailable: {unavailable:,}")


if __name__ == "__main__":
    main()
