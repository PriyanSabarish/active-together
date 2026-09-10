"""Manually download a Monash VPA Open Space snapshot.

This utility is not part of the routine pipeline because Iteration 2 uses a
fixed source snapshot for reproducibility.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# Source and output paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "monash"

VPA_API_URL = (
    "https://services5.arcgis.com/DmRfik4clMVydXO3/"
    "arcgis/rest/services/"
    "VPA_Draft_Open_Space_Data/FeatureServer/0/query"
)


def main():
    """Download and save the current Monash VPA snapshot."""

    query = {
        "where": "LGA = 'MONASH'",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": 2000,
        "f": "geojson",
    }

    # Download all Monash polygons in one request.
    response = requests.get(
        VPA_API_URL,
        params=query,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])

    # Check the response before saving it.
    if data.get("type") != "FeatureCollection":
        raise ValueError("VPA response is not a GeoJSON FeatureCollection.")

    if not features:
        raise ValueError("VPA returned no Monash features.")

    feature_ids = [feature["properties"].get("FID") for feature in features]

    if any(feature_id is None for feature_id in feature_ids):
        raise ValueError("Some VPA records have no FID.")

    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError("The VPA response contains duplicate FIDs.")

    # Create dated output paths.
    snapshot_date = datetime.now().astimezone().date().isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_path = RAW_DIR / f"vpa_open_space_monash_{snapshot_date}.geojson"

    metadata_path = RAW_DIR / f"vpa_open_space_monash_{snapshot_date}.metadata.json"

    # Preserve an existing snapshot from the same day.
    if snapshot_path.exists() or metadata_path.exists():
        raise FileExistsError("Today's VPA snapshot already exists.")

    # Save the unmodified API response.
    with snapshot_path.open("x", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    metadata = {
        "dataset": "VPA Draft Open Space Data",
        "source_url": VPA_API_URL,
        "filter": "LGA = 'MONASH'",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": len(features),
        "snapshot_file": snapshot_path.name,
    }

    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("VPA records downloaded:", len(features))
    print("Snapshot saved:", snapshot_path)
    print("Metadata saved:", metadata_path)


if __name__ == "__main__":
    main()
