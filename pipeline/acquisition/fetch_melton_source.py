"""Manually download fixed Melton City Council source snapshots.

This utility is not part of the routine pipeline. Run it only when an
intentional source refresh will be followed by exploration and review.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# Fixed source definitions and output directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "melton"

DATASETS = {
    "open_space": {
        "dataset": "Melton Open Space",
        "url": (
            "https://data.gov.au/geoserver/melton-open-space/wfs"
            "?request=GetFeature"
            "&typeName=ckan_e3fb7007_d697_4c92_b3bb_4420478e5e1f"
            "&outputFormat=json"
        ),
        "filename": "melton_open_space_{date}.geojson",
    },
    "ovals_and_fields": {
        "dataset": "Melton Ovals and Fields",
        "url": (
            "https://data.gov.au/geoserver/melton-ovals-and-fields/wfs"
            "?request=GetFeature"
            "&typeName=ckan_91517082_af13_4663_84ce_604a92d24e86"
            "&outputFormat=json"
        ),
        "filename": "melton_ovals_and_fields_{date}.geojson",
    },
}


def fetch_geojson(source):
    """Download and minimally check one official GeoJSON response."""

    response = requests.get(source["url"], timeout=60)
    response.raise_for_status()
    data = response.json()

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{source['dataset']} did not return a FeatureCollection.")
    if not data.get("features"):
        raise ValueError(f"{source['dataset']} returned no records.")

    return data


def main():
    """Save both reviewed sources as dated, immutable snapshots."""

    snapshot_date = datetime.now().astimezone().date().isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        key: RAW_DIR / source["filename"].format(date=snapshot_date)
        for key, source in DATASETS.items()
    }
    metadata_path = RAW_DIR / f"melton_sources_{snapshot_date}.metadata.json"

    # Preserve all existing snapshots from the same date.
    existing = [path for path in [*outputs.values(), metadata_path] if path.exists()]
    if existing:
        raise FileExistsError(f"Snapshot already exists: {existing[0]}")

    downloaded = {
        key: fetch_geojson(source)
        for key, source in DATASETS.items()
    }

    metadata = {
        "provider": "Melton City Council via data.gov.au",
        "license": "Creative Commons Attribution 2.5 Australia",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_coordinate_system": "EPSG:28355",
        "source_crs_note": (
            "The GeoJSON is labelled EPSG:4326 but its coordinates are "
            "MGA Zone 55 (EPSG:28355). Processing overrides the label."
        ),
        "datasets": {},
    }

    for key, source in DATASETS.items():
        data = downloaded[key]

        # Save the unmodified official response.
        with outputs[key].open("x", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, separators=(",", ":"))

        metadata["datasets"][key] = {
            "dataset": source["dataset"],
            "source_url": source["url"],
            "record_count": len(data["features"]),
            "snapshot_file": outputs[key].name,
        }

        print(f"{source['dataset']} records:", len(data["features"]))
        print("Snapshot saved:", outputs[key])

    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    print("Metadata saved:", metadata_path)


if __name__ == "__main__":
    main()
