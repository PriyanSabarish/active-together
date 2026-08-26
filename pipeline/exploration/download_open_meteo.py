"""Download Open-Meteo exploration snapshots for Greater Melbourne."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


MELBOURNE_SITES = (
    ("melbourne_cbd", -37.8136, 144.9631),
    ("werribee", -37.9000, 144.6610),
    ("sunbury", -37.5797, 144.7280),
    ("craigieburn", -37.5989, 144.9418),
    ("lilydale", -37.7570, 145.3550),
    ("pakenham", -38.0702, 145.4751),
    ("frankston", -38.1499, 145.1220),
    ("dandenong", -37.9875, 145.2148),
    ("ringwood", -37.8150, 145.2290),
)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def build_url(base_url: str, hourly: str, forecast_days: int) -> str:
    params = {
        "latitude": ",".join(str(site[1]) for site in MELBOURNE_SITES),
        "longitude": ",".join(str(site[2]) for site in MELBOURNE_SITES),
        "hourly": hourly,
        "timezone": ",".join("Australia/Sydney" for _ in MELBOURNE_SITES),
        "forecast_days": str(forecast_days),
    }
    return f"{base_url}?{urlencode(params)}"


def download_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": "active-together-data-pipeline/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def add_site_names(payload: object) -> object:
    if not isinstance(payload, list) or len(payload) != len(MELBOURNE_SITES):
        raise ValueError("Open-Meteo returned an unexpected number of locations")
    for record, (site_name, requested_latitude, requested_longitude) in zip(
        payload, MELBOURNE_SITES, strict=True
    ):
        record["site_name"] = site_name
        record["requested_latitude"] = requested_latitude
        record["requested_longitude"] = requested_longitude
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
    args = parser.parse_args()

    snapshot_date = datetime.now(ZoneInfo("Australia/Sydney")).date().isoformat()
    forecast_url = build_url(
        FORECAST_URL,
        "temperature_2m,apparent_temperature,precipitation_probability,"
        "weather_code,wind_speed_10m,wind_gusts_10m",
        forecast_days=7,
    )
    air_quality_url = build_url(
        AIR_QUALITY_URL, "uv_index,pm2_5,pm10", forecast_days=5
    )

    forecast = add_site_names(download_json(forecast_url))
    air_quality = add_site_names(download_json(air_quality_url))

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
        },
    )

    print(f"Wrote {forecast_path}")
    print(f"Wrote {air_quality_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
