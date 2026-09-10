# Monash VPA Open Space Acquisition

## Purpose

`fetch_monash_source.py` documents how the Monash subset of the VPA Draft Open
Space dataset was acquired. It downloads source data only and does not clean,
match or update location names.

The VPA dataset is no longer actively maintained. The routine Iteration 2
pipeline therefore uses a fixed snapshot instead of downloading the source on
every run.

## Fixed source snapshot

```text
data/raw/monash/vpa_open_space_monash_2026-09-10.geojson
data/raw/monash/vpa_open_space_monash_2026-09-10.metadata.json
```

The snapshot contains 831 Monash polygons in EPSG:4326. The metadata records
the source endpoint, filter, retrieval time and record count. Both files are
kept with the project so the result remains reproducible if the online service
later changes or becomes unavailable.

## Optional manual acquisition

Run the script only when intentionally acquiring a replacement snapshot:

```text
python pipeline/acquisition/fetch_monash_source.py
```

The script requests records where `LGA = 'MONASH'`, checks the GeoJSON response,
missing IDs and duplicate IDs, and saves dated source and metadata files. It
does not overwrite an existing snapshot from the same date.

A replacement snapshot must first be explored and validated. The fixed paths
in the wrangling and validation scripts must then be deliberately updated.

## Data source

- Dataset: VPA Draft Open Space Data
- Provider: Victorian Planning Authority
- Service: ArcGIS Feature Service
- Filter: `LGA = 'MONASH'`
- Output coordinate system: EPSG:4326
- Endpoint: `https://services5.arcgis.com/DmRfik4clMVydXO3/arcgis/rest/services/VPA_Draft_Open_Space_Data/FeatureServer/0/query`

## Pipeline role

```text
fixed VPA snapshot
        ↓
wrangle_monash_names.py
        ↓
vicmap_app_ready_monash_enriched.csv
        ↓
validate_monash_names.py
```

Acquisition is optional and is not part of the routine processing workflow.
