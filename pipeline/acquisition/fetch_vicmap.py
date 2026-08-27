"""Fetch and validate Vicmap Features of Interest WFS data."""

# 1. Imports
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# 2. Project paths and WFS configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_VICMAP_DIR = PROJECT_ROOT / "data" / "raw" / "vicmap"

WFS_ENDPOINT = "https://opendata.maps.vic.gov.au/geoserver/wfs"
WFS_LAYER = "open-data-platform:foi_index_centroid"
WFS_VERSION = "2.0.0"
OUTPUT_CRS = "EPSG:4326"

TEST_RECORD_COUNT = 5
DEFAULT_PAGE_SIZE = 5_000
REQUEST_TIMEOUT_SECONDS = 60


# 3. Request functions
def build_request_url(count, start_index=0):
    """Build one bounded WFS GetFeature request URL."""

    parameters = {
        "service": "WFS",
        "version": WFS_VERSION,
        "request": "GetFeature",
        "typeNames": WFS_LAYER,
        "outputFormat": "application/json",
        "srsName": OUTPUT_CRS,
        "count": count,
        "startIndex": start_index,
    }

    return f"{WFS_ENDPOINT}?{urlencode(parameters)}"


def fetch_page(count, start_index=0):
    """Fetch and validate one GeoJSON page from the WFS API."""

    request_url = build_request_url(count=count, start_index=start_index)
    request = Request(
        request_url,
        headers={"User-Agent": "active-together-data-pipeline/1.0"},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response_content_type = response.headers.get_content_type()
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"Vicmap WFS returned HTTP {error.code}: {error.reason}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"Could not connect to the Vicmap WFS API: {error.reason}"
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Vicmap WFS did not return valid JSON.") from error

    if payload.get("type") != "FeatureCollection":
        raise ValueError("Vicmap WFS response is not a GeoJSON FeatureCollection.")

    features = payload.get("features")

    if not isinstance(features, list):
        raise ValueError("Vicmap WFS response does not contain a feature list.")

    return payload, response_content_type, request_url


# 4. Connection test
def run_connection_test():
    """Fetch five records without writing any files."""

    payload, content_type, request_url = fetch_page(
        count=TEST_RECORD_COUNT,
        start_index=0,
    )
    features = payload["features"]

    if len(features) != TEST_RECORD_COUNT:
        raise ValueError(
            "Unexpected test record count. "
            f"Expected {TEST_RECORD_COUNT}, received {len(features)}."
        )

    print(f"WFS layer: {WFS_LAYER}")
    print(f"Response content type: {content_type}")
    print(f"GeoJSON type: {payload['type']}")
    print(f"Total records available: {payload.get('numberMatched', 'not provided')}")
    print(f"Records returned: {len(features)}")
    print(f"Test request URL: {request_url}")
    print("API connection test completed successfully.")


# 5. Full snapshot functions
def parse_total_records(payload):
    """Return the integer record total reported by the WFS response."""

    reported_total = payload.get("numberMatched", payload.get("totalFeatures"))

    try:
        total_records = int(reported_total)
    except (TypeError, ValueError) as error:
        raise ValueError("WFS response did not provide a valid record total.") from error

    if total_records <= 0:
        raise ValueError("WFS response reported no available records.")

    return total_records


def download_all_records(page_size):
    """Download all WFS records using deterministic pagination."""

    first_page, content_type, first_request_url = fetch_page(
        count=page_size,
        start_index=0,
    )
    total_records = parse_total_records(first_page)
    all_features = list(first_page["features"])

    print(f"Total records reported by API: {total_records:,}")
    print(f"Downloaded records: {len(all_features):,} / {total_records:,}")

    while len(all_features) < total_records:
        start_index = len(all_features)
        page, _, _ = fetch_page(
            count=page_size,
            start_index=start_index,
        )
        page_features = page["features"]

        if not page_features:
            raise ValueError(
                "WFS pagination returned an empty page before the reported total."
            )

        all_features.extend(page_features)
        print(f"Downloaded records: {len(all_features):,} / {total_records:,}")

    if len(all_features) != total_records:
        raise ValueError(
            "Downloaded record count does not match the WFS total. "
            f"Expected {total_records:,}, received {len(all_features):,}."
        )

    feature_ids = [feature.get("id") for feature in all_features]

    if any(feature_id is None for feature_id in feature_ids):
        raise ValueError("Downloaded Vicmap features contain missing feature IDs.")

    duplicate_id_count = len(feature_ids) - len(set(feature_ids))

    if duplicate_id_count:
        raise ValueError(
            f"Downloaded Vicmap features contain {duplicate_id_count:,} duplicate IDs."
        )

    snapshot = {
        "type": "FeatureCollection",
        "features": all_features,
        "totalFeatures": total_records,
        "numberMatched": total_records,
        "numberReturned": len(all_features),
        "timeStamp": first_page.get("timeStamp"),
        "crs": first_page.get("crs"),
    }

    print("Full WFS download validated successfully.")

    return snapshot, {
        "content_type": content_type,
        "first_request_url": first_request_url,
        "record_count": total_records,
        "source_timestamp": first_page.get("timeStamp"),
    }


def calculate_sha256(file_path):
    """Calculate a SHA-256 checksum without loading the file into memory."""

    checksum = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            checksum.update(chunk)

    return checksum.hexdigest()


def save_snapshot(snapshot, download_details, page_size):
    """Write a dated snapshot and metadata without overwriting existing files."""

    snapshot_date = datetime.now().astimezone().date().isoformat()
    snapshot_name = f"foi_index_centroid_full_{snapshot_date}.geojson"
    metadata_name = f"foi_index_centroid_full_{snapshot_date}.metadata.json"

    RAW_VICMAP_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_path = RAW_VICMAP_DIR / snapshot_name
    metadata_path = RAW_VICMAP_DIR / metadata_name

    existing_paths = [
        path for path in [snapshot_path, metadata_path] if path.exists()
    ]

    if existing_paths:
        existing_names = ", ".join(path.name for path in existing_paths)
        raise FileExistsError(
            "Snapshot output already exists and will not be overwritten: "
            f"{existing_names}"
        )

    temporary_path = None

    try:
        # Write to a temporary file before publishing the validated snapshot
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=RAW_VICMAP_DIR,
            prefix=f".{snapshot_name}.",
            suffix=".part",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(
                snapshot,
                temporary_file,
                ensure_ascii=False,
                separators=(",", ":"),
            )

        checksum = calculate_sha256(temporary_path)

        # Path.rename fails rather than replacing the existing file on Windows
        temporary_path.rename(snapshot_path)
        temporary_path = None

        metadata = {
            "dataset": "Vicmap Features of Interest Index Centroid",
            "wfs_endpoint": WFS_ENDPOINT,
            "wfs_layer": WFS_LAYER,
            "wfs_version": WFS_VERSION,
            "output_crs": OUTPUT_CRS,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_timestamp": download_details["source_timestamp"],
            "record_count": download_details["record_count"],
            "page_size": page_size,
            "content_type": download_details["content_type"],
            "first_request_url": download_details["first_request_url"],
            "snapshot_file": snapshot_path.name,
            "sha256": checksum,
        }

        with metadata_path.open("x", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)
            metadata_file.write("\n")
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    print(f"Raw snapshot saved: {snapshot_path}")
    print(f"Snapshot metadata saved: {metadata_path}")
    print(f"SHA-256: {checksum}")

    return snapshot_path, metadata_path


def run_full_download(page_size):
    """Download, validate and save a complete dated raw snapshot."""

    if page_size <= 0:
        raise ValueError("Page size must be a positive integer.")

    snapshot_date = datetime.now().astimezone().date().isoformat()
    expected_snapshot_path = (
        RAW_VICMAP_DIR / f"foi_index_centroid_full_{snapshot_date}.geojson"
    )
    expected_metadata_path = (
        RAW_VICMAP_DIR / f"foi_index_centroid_full_{snapshot_date}.metadata.json"
    )

    # Stop before downloading if today's snapshot already exists
    if expected_snapshot_path.exists() or expected_metadata_path.exists():
        raise FileExistsError(
            "Today's Vicmap snapshot already exists and will not be overwritten."
        )

    snapshot, download_details = download_all_records(page_size=page_size)
    save_snapshot(
        snapshot=snapshot,
        download_details=download_details,
        page_size=page_size,
    )
    print("Vicmap acquisition completed successfully.")


# 6. Command-line interface
def parse_arguments():
    """Parse explicit test or full-download options."""

    parser = argparse.ArgumentParser(
        description="Test or download the Vicmap FOI WFS dataset."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download and save the complete dated raw snapshot.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"WFS records requested per page (default: {DEFAULT_PAGE_SIZE}).",
    )

    return parser.parse_args()


# 7. Script entry point
def main():
    """Run a safe connection test or an explicit full download."""

    arguments = parse_arguments()

    if arguments.download:
        run_full_download(page_size=arguments.page_size)
    else:
        run_connection_test()


if __name__ == "__main__":
    main()
