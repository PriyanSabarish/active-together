
# Data Guide

## Start here

This document explains which data files are intended for use by the application.

For the current product, the main geographic scope is:

- Melbourne
- Melton
- Monash

## App-ready data

### Vicmap activity locations

File:

`data/processed/vicmap/vicmap_app_ready.csv`

This is the main Vicmap dataset for the application.

It contains locations that:

- are inside Melbourne, Melton or Monash;
- belong to one of the seven supported activity categories;
- passed the current wrangling and validation rules; and
- are approved for normal recommendations.

Application developers should use this file as the primary Vicmap input.

Current activity categories:

- `playground`
- `park_and_garden`
- `sports_ground`
- `court`
- `trail_access`
- `skate_bmx`
- `picnic_day_use`

Important columns:

| Column                       | Description                        |
|---|---|
| `place_id`                   | Unique location identifier         |
| `display_name`               | Name to display in the application |
| `activity_category`          | Application activity category      |
| `lga_name`                   | Council name                       |
| `longitude`                  | Longitude in EPSG:4326             |
| `latitude`                   | Latitude in EPSG:4326              |
| `classification_confidence`  | Confidence in the category mapping |
| `source_dataset`             | Original source dataset            |
| `source_record_id`           | Identifier from the source dataset |

## Fallback data

File:

`data/processed/vicmap/vicmap_fallback.csv`

This file contains potentially useful places that may have:

- access restrictions;
- booking requirements;
- membership requirements;
- entry fees; or
- uncertain operating conditions.

Do not mix these records directly into normal recommendations.

The application should only use this file if it has explicit fallback behaviour or can communicate the uncertainty to users.

## Files not intended for direct application use

### Raw data

Location:

`data/raw/`

These files are original source snapshots. They are retained for reproducibility and should not be loaded directly by the application.

Vicmap FOI snapshots and their metadata remain local and are not committed to GitHub.

### Fixed LGA boundary

The pipeline uses the versioned spatial reference:

`data/raw/boundaries/vicmap_lga_2026-08-26.geojson`

This relatively stable boundary file is committed to the repository because wrangling and validation both require it. Routine FOI refreshes do not replace the boundary. A boundary update should be an explicit, reviewed change because it may alter council assignments.

### Greater Melbourne master data

Location:

`data/processed/vicmap/`

Files containing `greater_melbourne` are reusable master datasets covering 31 metropolitan councils.

They are retained in case the product scope changes. The current application should use `vicmap_app_ready.csv` instead.

### Validation files

Location:

`data/validation/vicmap/`

These files contain:

- classification rules;
- duplicate-review records;
- manual review decisions;
- QA samples; and
- unresolved low-priority name-enrichment candidates.

They support auditing and data maintenance and are not direct application inputs.

## Updating the data

The current processed files are generated from dated Vicmap WFS GeoJSON snapshots.

To download a new FOI snapshot and run the complete workflow from the project root:

```powershell
python pipeline/run_vicmap_pipeline.py --refresh
```

To rerun wrangling and validation using the latest existing local snapshot:

```powershell
python pipeline/run_vicmap_pipeline.py
```

The unified runner stops when acquisition, wrangling or validation fails. Product files should be shared with the application only after validation succeeds.

## Technical documentation

Detailed technical documentation is available at:

- `pipeline/README.md`
- `pipeline/acquisition/README.md`
- `pipeline/exploration/README.md`
- `pipeline/wrangling/README.md`
- `pipeline/validation/README.md`

Most team members only need this data guide and the app-ready CSV.



























