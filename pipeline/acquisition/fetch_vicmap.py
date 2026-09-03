"""Download a complete Vicmap Features of Interest snapshot."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# Vicmap WFS settings
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "vicmap"

WFS_ENDPOINT = "https://opendata.maps.vic.gov.au/geoserver/wfs"
WFS_LAYER = "open-data-platform:foi_index_centroid"
WFS_VERSION = "2.0.0"
OUTPUT_CRS = "EPSG:4326"

DEFAULT_PAGE_SIZE = 5_000
REQUEST_TIMEOUT = 60


def build_url(record_count, start_index=0):
    """Build one WFS GetFeature request URL."""

    parameters = {
        "service": "WFS",
        "version": WFS_VERSION,
        "request": "GetFeature",
        "typeNames": WFS_LAYER,
        "outputFormat": "application/json",
        "srsName": OUTPUT_CRS,
        "count": record_count,
        "startIndex": start_index,
    }
    return f"{WFS_ENDPOINT}?{urlencode(parameters)}"


def fetch_page(record_count, start_index=0):
    """Download and check one page of GeoJSON records."""

    request_url = build_url(record_count, start_index)
    request = Request(
        request_url,
        headers={"User-Agent": "active-together-data-pipeline/1.0"},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Vicmap returned HTTP {error.code}: {error.reason}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to Vicmap: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Vicmap did not return valid JSON.") from error

    if payload.get("type") != "FeatureCollection":
        raise ValueError("Vicmap response is not a GeoJSON FeatureCollection.")
    if not isinstance(payload.get("features"), list):
        raise ValueError("Vicmap response does not contain a feature list.")

    return payload


def get_total_records(payload):
    """Read the total number of records reported by Vicmap."""

    reported_total = payload.get("numberMatched", payload.get("totalFeatures"))

    try:
        total_records = int(reported_total)
    except (TypeError, ValueError) as error:
        raise ValueError("Vicmap did not provide a valid record total.") from error

    if total_records <= 0:
        raise ValueError("Vicmap reported no available records.")

    return total_records


def download_all_records(page_size):
    """Download every record using WFS pagination."""

    first_page = fetch_page(page_size, start_index=0)
    total_records = get_total_records(first_page)
    all_features = list(first_page["features"])

    print(f"Total records reported: {total_records:,}")
    print(f"Downloaded: {len(all_features):,} / {total_records:,}")

    while len(all_features) < total_records:
        next_page = fetch_page(page_size, start_index=len(all_features))
        new_features = next_page["features"]

        if not new_features:
            raise ValueError("Vicmap returned an empty page before completion.")

        all_features.extend(new_features)
        print(f"Downloaded: {len(all_features):,} / {total_records:,}")

    if len(all_features) != total_records:
        raise ValueError(
            f"Expected {total_records:,} records but received {len(all_features):,}."
        )

    # Feature IDs confirm that pagination did not repeat a page.
    feature_ids = [feature.get("id") for feature in all_features]

    if any(feature_id is None for feature_id in feature_ids):
        raise ValueError("Some downloaded features have no source ID.")
    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError("The complete download contains duplicate feature IDs.")

    snapshot = {
        "type": "FeatureCollection",
        "features": all_features,
        "totalFeatures": total_records,
        "numberMatched": total_records,
        "numberReturned": len(all_features),
        "timeStamp": first_page.get("timeStamp"),
        "crs": first_page.get("crs"),
    }

    print("Complete download passed record checks.")
    return snapshot


def output_paths():
    """Return today's snapshot and metadata paths."""

    today = datetime.now().astimezone().date().isoformat()
    base_name = f"foi_index_centroid_full_{today}"

    return (
        RAW_DIR / f"{base_name}.geojson",
        RAW_DIR / f"{base_name}.metadata.json",
    )


def save_snapshot(snapshot, page_size):
    """Save a dated snapshot without replacing an existing download."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path, metadata_path = output_paths()

    if snapshot_path.exists() or metadata_path.exists():
        raise FileExistsError(
            "Today's Vicmap snapshot already exists and will not be overwritten."
        )

    with snapshot_path.open("x", encoding="utf-8") as output_file:
        json.dump(snapshot, output_file, ensure_ascii=False, separators=(",", ":"))

    metadata = {
        "dataset": "Vicmap Features of Interest Index Centroid",
        "wfs_endpoint": WFS_ENDPOINT,
        "wfs_layer": WFS_LAYER,
        "wfs_version": WFS_VERSION,
        "output_crs": OUTPUT_CRS,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_timestamp": snapshot.get("timeStamp"),
        "record_count": len(snapshot["features"]),
        "page_size": page_size,
        "snapshot_file": snapshot_path.name,
    }

    with metadata_path.open("x", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)
        metadata_file.write("\n")

    print(f"Raw snapshot saved: {snapshot_path}")
    print(f"Metadata saved: {metadata_path}")


def run_connection_test():
    """Download five records without saving a file."""

    payload = fetch_page(record_count=5)
    total_records = get_total_records(payload)

    if len(payload["features"]) != 5:
        raise ValueError("The connection test did not return five records.")

    print(f"WFS layer: {WFS_LAYER}")
    print(f"Total records available: {total_records:,}")
    print("API connection test completed successfully.")


def run_download(page_size):
    """Check the output path, download all records and save them."""

    snapshot_path, metadata_path = output_paths()

    # Stop before making API requests when today's files already exist.
    if snapshot_path.exists() or metadata_path.exists():
        raise FileExistsError(
            "Today's Vicmap snapshot already exists and will not be overwritten."
        )

    snapshot = download_all_records(page_size)
    save_snapshot(snapshot, page_size)
    print("Vicmap acquisition completed successfully.")


def parse_arguments():
    """Read the test or download command-line options."""

    parser = argparse.ArgumentParser(
        description="Test or download the Vicmap FOI WFS dataset."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download and save the complete dated snapshot.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"Records requested per page (default: {DEFAULT_PAGE_SIZE}).",
    )

    arguments = parser.parse_args()

    if arguments.page_size <= 0:
        parser.error("--page-size must be a positive integer.")

    return arguments


def main():
    """Run a connection test or a complete download."""

    arguments = parse_arguments()

    if arguments.download:
        run_download(arguments.page_size)
    else:
        run_connection_test()


if __name__ == "__main__":
    main()
