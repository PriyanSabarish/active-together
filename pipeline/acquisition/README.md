# Vicmap Data Acquisition

## Purpose

This directory contains the data-acquisition step for the Vicmap Features of Interest dataset.

The acquisition script connects to the Vicmap WFS API, downloads a complete raw GeoJSON snapshot and records metadata needed for reproducibility. It does not perform cleaning, classification or product filtering.

## Script

`pipeline/acquisition/fetch_vicmap.py`

Run commands from the project root.

## Connection test

Run the script without arguments to request five records:

```powershell
python pipeline/acquisition/fetch_vicmap.py
```

This mode:

- checks that the WFS endpoint is available;
- confirms that the configured layer exists;
- validates the GeoJSON response structure;
- reports the total number of available records; and
- does not create or modify any files.

## Complete snapshot download

Use the explicit download option to retrieve the complete dataset:

```powershell
python pipeline/acquisition/fetch_vicmap.py --download
```

The script requests the data in pages of 5,000 records, combines the pages and validates:

- the reported and downloaded record counts;
- the GeoJSON `FeatureCollection` structure;
- the presence of feature IDs; and
- the absence of duplicate feature IDs.

The page size can be changed when diagnosing an API limitation:

```powershell
python pipeline/acquisition/fetch_vicmap.py --download --page-size 2000
```

The default page size should normally be retained.

## Data source

- Dataset: Vicmap Features of Interest Index Centroid
- WFS endpoint: `https://opendata.maps.vic.gov.au/geoserver/wfs`
- Layer: `open-data-platform:foi_index_centroid`
- WFS version: 2.0.0
- Output format: GeoJSON
- Output coordinate reference system: EPSG:4326

## Output files

Successful downloads are written to:

`data/raw/vicmap/`

The snapshot filename follows this convention:

```text
foi_index_centroid_full_YYYY-MM-DD.geojson
```

A metadata sidecar is created with the same date:

```text
foi_index_centroid_full_YYYY-MM-DD.metadata.json
```

The metadata records:

- the WFS endpoint, layer and version;
- the download timestamp;
- the timestamp reported by the source;
- the record count and page size;
- the output coordinate system; and
- the snapshot filename.

Raw snapshots and metadata are excluded from GitHub by `.gitignore`. They are retained locally for reproducibility and should be managed according to the project data management plan.

## File-safety rules

The acquisition process is designed to preserve existing raw data:

- the default test mode never writes files;
- complete snapshots use a date in the filename;
- an existing snapshot or metadata file is never overwritten;
- the script stops before downloading if today's output already exists;
- downloaded data is checked before it is saved.

If today's snapshot already exists, do not delete it merely to repeat the command. Confirm whether a new download is necessary and preserve the existing snapshot where possible.

## Relationship to the pipeline

The acquisition script only creates the raw source snapshot. The remaining processing stages are separate:

```text
Vicmap WFS API
      ↓
pipeline/acquisition/fetch_vicmap.py
      ↓
data/raw/vicmap/foi_index_centroid_full_YYYY-MM-DD.geojson
      ↓
pipeline/wrangling/wrangle_vicmap.py
      ↓
data/processed/vicmap/vicmap_app_ready.csv
      ↓
pipeline/validation/validate_vicmap.py
```

The wrangling script automatically selects the complete raw snapshot with the latest date in its filename.

## Manual refresh workflow

Use the unified pipeline runner to process the latest existing raw snapshot:

```powershell
python pipeline/run_vicmap_pipeline.py
```

To explicitly download a new snapshot before processing, run:

```powershell
python pipeline/run_vicmap_pipeline.py --refresh
```

The unified runner stops immediately if acquisition, wrangling or validation fails.

The same workflow can also be run as separate commands when diagnosing an individual stage:

```powershell
python pipeline/acquisition/fetch_vicmap.py --download
python pipeline/wrangling/wrangle_vicmap.py
python pipeline/validation/validate_vicmap.py
```

New processed data should be shared with the application only after validation completes successfully.

## Failure handling

If an API request fails:

- the script reports the HTTP or connection error;
- no completed raw snapshot is published;
- existing raw snapshots remain unchanged; and
- wrangling can continue using the latest previously validated snapshot.

If the API introduces new records or subtypes, wrangling or validation may stop for review. This is expected behaviour and prevents unreviewed source changes from silently entering the product output.
