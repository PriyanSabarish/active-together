"""Manually download fixed City of Melbourne source snapshots.

This utility is not part of the routine pipeline. Run it only when an
intentional source refresh will be followed by exploration and review.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# Source and output paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "melbourne"

API_BASE = (
    "https://data.melbourne.vic.gov.au/"
    "api/explore/v2.1/catalog/datasets"
)

DATASETS = {
    "playgrounds": "playgrounds",
    "landmarks": (
        "landmarks-and-places-of-interest-"
        "including-schools-theatres-health-"
        "services-spor"
    ),
}


def fetch_geojson(dataset_id):
    """Download and minimally check one GeoJSON dataset."""

    url = f"{API_BASE}/{dataset_id}/exports/geojson"
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{dataset_id} did not return a FeatureCollection.")
    if not features:
        raise ValueError(f"{dataset_id} returned no records.")

    return data, url


def main():
    """Download both official sources as dated fixed snapshots."""

    snapshot_date = datetime.now().astimezone().date().isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        key: RAW_DIR / f"city_of_melbourne_{key}_{snapshot_date}.geojson"
        for key in DATASETS
    }
    metadata_path = (
        RAW_DIR
        / f"city_of_melbourne_sources_{snapshot_date}.metadata.json"
    )

    # Preserve all existing snapshots from the same date.
    existing = [path for path in [*outputs.values(), metadata_path] if path.exists()]
    if existing:
        raise FileExistsError(f"Snapshot already exists: {existing[0]}")

    metadata = {
        "provider": "City of Melbourne Open Data Portal",
        "license": "CC BY",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": {},
    }

    for key, dataset_id in DATASETS.items():
        data, source_url = fetch_geojson(dataset_id)

        # Save the unmodified API response.
        with outputs[key].open("x", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, separators=(",", ":"))

        metadata["datasets"][key] = {
            "dataset_id": dataset_id,
            "source_url": source_url,
            "record_count": len(data["features"]),
            "snapshot_file": outputs[key].name,
        }

        print(f"{key.title()} records downloaded:", len(data["features"]))
        print("Snapshot saved:", outputs[key])

    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    print("Metadata saved:", metadata_path)


if __name__ == "__main__":
    main()
