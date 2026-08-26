
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

The current processed files were generated from a saved Vicmap WFS GeoJSON snapshot.

To regenerate the data:

1. obtain the latest raw Vicmap snapshot;
2. run `pipeline/wrangling/wrangle_vicmap.py`;
3. run `pipeline/validation/validate_vicmap.py`;
4. confirm that validation completes successfully; and
5. replace the application data only after the checks pass.

## Technical documentation

Detailed technical documentation is available at:

- `pipeline/exploration/README.md`
- `pipeline/wrangling/README.md`
- `pipeline/validation/README.md`

Most team members only need this data guide and the app-ready CSV.



























