"""Download Open-Meteo exploration snapshots for Greater Melbourne."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
DEFAULT_LOCATIONS_FILE = (
    Path(__file__).resolve().parents[1] / "config" / "open_meteo_locations.csv"
)


def load_locations(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as handle:
        locations = list(csv.DictReader(handle))
    if not locations:
        raise ValueError(f"No locations found in {path}")
    if len({row["site_name"] for row in locations}) != len(locations):
        raise ValueError("site_name values must be unique")
    for row in locations:
        row["latitude"] = float(row["latitude"])
        row["longitude"] = float(row["longitude"])
    return locations


def build_url(
    base_url: str,
    hourly: str,
    forecast_days: int,
    locations: list[dict[str, object]],
) -> str:
    params = {
        "latitude": ",".join(str(site["latitude"]) for site in locations),
        "longitude": ",".join(str(site["longitude"]) for site in locations),
        "hourly": hourly,
        "timezone": ",".join("Australia/Sydney" for _ in locations),
        "forecast_days": str(forecast_days),
    }
    return f"{base_url}?{urlencode(params)}"


def download_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": "active-together-data-pipeline/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def add_site_names(payload: object, locations: list[dict[str, object]]) -> object:
    if not isinstance(payload, list) or len(payload) != len(locations):
        raise ValueError("Open-Meteo returned an unexpected number of locations")
    for record, location in zip(payload, locations, strict=True):
        record["site_name"] = location["site_name"]
        record["display_name"] = location["display_name"]
        record["lga_code"] = location["lga_code"]
        record["requested_latitude"] = location["latitude"]
        record["requested_longitude"] = location["longitude"]
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary_path.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "raw" / "open_meteo",
    )
    parser.add_argument(
        "--locations-file", type=Path, default=DEFAULT_LOCATIONS_FILE
    )
    args = parser.parse_args()
    locations = load_locations(args.locations_file)

    snapshot_date = datetime.now(ZoneInfo("Australia/Sydney")).date().isoformat()
    forecast_url = build_url(
        FORECAST_URL,
        "temperature_2m,apparent_temperature,precipitation_probability,"
        "weather_code,wind_speed_10m,wind_gusts_10m",
        forecast_days=7,
        locations=locations,
    )
    air_quality_url = build_url(
        AIR_QUALITY_URL,
        "uv_index,pm2_5,pm10",
        forecast_days=5,
        locations=locations,
    )

    forecast = add_site_names(download_json(forecast_url), locations)
    air_quality = add_site_names(download_json(air_quality_url), locations)

    forecast_path = args.output_dir / f"weather_forecast_{snapshot_date}.json"
    air_quality_path = args.output_dir / f"air_quality_{snapshot_date}.json"
    manifest_path = args.output_dir / f"download_manifest_{snapshot_date}.json"

    write_json(forecast_path, forecast)
    write_json(air_quality_path, air_quality)
    write_json(
        manifest_path,
        {
            "retrieved_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
            "licence": "CC BY 4.0",
            "attribution": "Weather data by Open-Meteo.com",
            "forecast_url": forecast_url,
            "air_quality_url": air_quality_url,
            "files": [forecast_path.name, air_quality_path.name],
            "location_count": len(locations),
            "locations_file": str(args.locations_file),
            "geographic_scope": "31 Metropolitan Melbourne municipalities",
        },
    )

    print(f"Wrote {forecast_path}")
    print(f"Wrote {air_quality_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
