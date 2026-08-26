"""Explore the downloaded Open-Meteo weather and air-quality snapshots.

Run from any working directory. Summary CSV files are written to
data/processed/open_meteo/exploration. PNG charts are also produced when
matplotlib is installed; the statistical exploration does not depend on it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "raw" / "open_meteo"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "processed" / "open_meteo" / "exploration"


def latest_snapshot(raw_dir: Path, prefix: str) -> Path:
    """Return the most recent date-stamped source file for one dataset."""
    candidates = sorted(raw_dir.glob(f"{prefix}_????-??-??.json"))
    if not candidates:
        raise FileNotFoundError(f"No {prefix} snapshot found in {raw_dir}")
    return candidates[-1]


def flatten_hourly_json(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    """Convert Open-Meteo's list-of-locations JSON into tidy hourly rows."""
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"Expected a non-empty list in {path}")

    frames: list[pd.DataFrame] = []
    units: dict[str, str] = {}
    for location in records:
        hourly = pd.DataFrame(location["hourly"])
        hourly.insert(0, "site_name", location["site_name"])
        hourly.insert(1, "requested_latitude", location["requested_latitude"])
        hourly.insert(2, "requested_longitude", location["requested_longitude"])
        hourly.insert(3, "grid_latitude", location["latitude"])
        hourly.insert(4, "grid_longitude", location["longitude"])
        frames.append(hourly)
        units.update(location.get("hourly_units", {}))

    data = pd.concat(frames, ignore_index=True)
    data["time"] = pd.to_datetime(data["time"], errors="raise")
    return data, units


def quality_report(data: pd.DataFrame) -> pd.DataFrame:
    """Summarise type, completeness, uniqueness, and numeric range by column."""
    rows = []
    for column in data.columns:
        series = data[column]
        numeric = pd.api.types.is_numeric_dtype(series)
        rows.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "rows": len(series),
                "missing": int(series.isna().sum()),
                "missing_pct": round(float(series.isna().mean() * 100), 3),
                "unique": int(series.nunique(dropna=True)),
                "min": series.min() if numeric else None,
                "max": series.max() if numeric else None,
            }
        )
    return pd.DataFrame(rows)


def validate_hourly_panel(data: pd.DataFrame) -> pd.DataFrame:
    """Check duplicates, ordering, and gaps separately for every site."""
    rows = []
    for site_name, site in data.groupby("site_name", sort=True):
        ordered = site.sort_values("time")
        gaps = ordered["time"].diff().dropna()
        rows.append(
            {
                "site_name": site_name,
                "rows": len(ordered),
                "start": ordered["time"].min(),
                "end": ordered["time"].max(),
                "duplicate_timestamps": int(ordered["time"].duplicated().sum()),
                "non_hourly_gaps": int((gaps != pd.Timedelta(hours=1)).sum()),
            }
        )
    return pd.DataFrame(rows)


def weather_summary(weather: pd.DataFrame) -> pd.DataFrame:
    """Build site-level weather metrics useful for activity recommendation."""
    grouped = weather.groupby("site_name", sort=True)
    result = grouped.agg(
        observations=("time", "size"),
        temperature_mean_c=("temperature_2m", "mean"),
        temperature_min_c=("temperature_2m", "min"),
        temperature_max_c=("temperature_2m", "max"),
        apparent_temperature_mean_c=("apparent_temperature", "mean"),
        precipitation_probability_mean_pct=("precipitation_probability", "mean"),
        precipitation_probability_max_pct=("precipitation_probability", "max"),
        wind_speed_mean_kmh=("wind_speed_10m", "mean"),
        wind_speed_max_kmh=("wind_speed_10m", "max"),
        wind_gusts_max_kmh=("wind_gusts_10m", "max"),
    )
    result["hours_precip_probability_ge_50"] = grouped[
        "precipitation_probability"
    ].apply(lambda values: int(values.ge(50).sum()))
    return result.reset_index().round(2)


def air_quality_summary(air: pd.DataFrame) -> pd.DataFrame:
    """Build site-level exposure summaries without making health claims."""
    grouped = air.groupby("site_name", sort=True)
    result = grouped.agg(
        observations=("time", "size"),
        uv_mean=("uv_index", "mean"),
        uv_max=("uv_index", "max"),
        pm2_5_mean_ugm3=("pm2_5", "mean"),
        pm2_5_max_ugm3=("pm2_5", "max"),
        pm10_mean_ugm3=("pm10", "mean"),
        pm10_max_ugm3=("pm10", "max"),
    )
    result["hours_uv_ge_3"] = grouped["uv_index"].apply(
        lambda values: int(values.ge(3).sum())
    )
    result["hours_uv_ge_6"] = grouped["uv_index"].apply(
        lambda values: int(values.ge(6).sum())
    )
    return result.reset_index().round(2)


def numeric_correlations(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Calculate pairwise Pearson correlations for selected numeric fields."""
    return data[columns].corr(method="pearson").round(3).rename_axis("variable")


def save_optional_charts(
    weather: pd.DataFrame, air: pd.DataFrame, output_dir: Path
) -> bool:
    """Save compact exploration plots when matplotlib is available."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    cbd_weather = weather.loc[weather["site_name"] == "melbourne_cbd"]
    figure, axis = plt.subplots(figsize=(11, 5))
    axis.plot(cbd_weather["time"], cbd_weather["temperature_2m"], label="Temperature")
    axis.plot(
        cbd_weather["time"],
        cbd_weather["apparent_temperature"],
        label="Apparent temperature",
    )
    axis.set(title="Melbourne CBD hourly weather", ylabel="Degrees Celsius")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(output_dir / "weather_cbd_temperature.png", dpi=160)
    plt.close(figure)

    air_long = air.melt(
        id_vars=["site_name", "time"],
        value_vars=["pm2_5", "pm10"],
        var_name="pollutant",
        value_name="concentration",
    )
    site_pollution = air_long.groupby(["site_name", "pollutant"])[
        "concentration"
    ].mean().unstack()
    axis = site_pollution.plot.bar(figsize=(11, 5))
    axis.set(
        title="Mean particulate concentration by site",
        ylabel="Concentration (micrograms per cubic metre)",
    )
    axis.grid(axis="y", alpha=0.25)
    figure = axis.get_figure()
    figure.tight_layout()
    figure.savefig(output_dir / "air_quality_site_particulates.png", dpi=160)
    plt.close(figure)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    weather_path = latest_snapshot(args.raw_dir, "weather_forecast")
    air_path = latest_snapshot(args.raw_dir, "air_quality")
    weather, weather_units = flatten_hourly_json(weather_path)
    air, air_units = flatten_hourly_json(air_path)

    outputs = {
        "weather_quality.csv": quality_report(weather),
        "air_quality_quality.csv": quality_report(air),
        "weather_panel_validation.csv": validate_hourly_panel(weather),
        "air_quality_panel_validation.csv": validate_hourly_panel(air),
        "weather_site_summary.csv": weather_summary(weather),
        "air_quality_site_summary.csv": air_quality_summary(air),
        "weather_correlations.csv": numeric_correlations(
            weather,
            [
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "wind_speed_10m",
                "wind_gusts_10m",
            ],
        ),
        "air_quality_correlations.csv": numeric_correlations(
            air, ["uv_index", "pm2_5", "pm10"]
        ),
    }
    for filename, table in outputs.items():
        table.to_csv(
            args.output_dir / filename,
            index=filename.endswith("_correlations.csv"),
        )

    metadata = {
        "weather_source_file": weather_path.name,
        "air_quality_source_file": air_path.name,
        "weather_rows": len(weather),
        "air_quality_rows": len(air),
        "site_count": int(weather["site_name"].nunique()),
        "weather_units": weather_units,
        "air_quality_units": air_units,
        "exploratory_thresholds": {
            "precipitation_probability_pct": 50,
            "uv_index_levels": [3, 6],
        },
        "threshold_note": "Exploratory flags only; they are not safety guarantees.",
    }
    (args.output_dir / "exploration_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    charts_created = save_optional_charts(weather, air, args.output_dir)
    print(f"Weather: {len(weather):,} rows, {weather['site_name'].nunique()} sites")
    print(f"Air quality: {len(air):,} rows, {air['site_name'].nunique()} sites")
    print(f"Output: {args.output_dir}")
    print("Charts: created" if charts_created else "Charts: skipped (matplotlib not installed)")


if __name__ == "__main__":
    main()
