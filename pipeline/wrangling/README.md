# Vicmap Data Wrangling

## Purpose

This directory contains the reproducible wrangling workflow used to transform the raw Vicmap Features of Interest dataset into:

1. reusable Greater Melbourne processed datasets; and
2. product-facing datasets for Melbourne, Melton and Monash.

The Greater Melbourne outputs are retained so that the product scope can be changed later without repeating the entire exploration and classification process.

## Wrangling script

The main script is:

`pipeline/wrangling/wrangle_vicmap.py`

Run it from the project root:

```powershell
python pipeline/wrangling/wrangle_vicmap.py
```

The script validates each major processing stage and stops if a required rule fails.

## Current data source
The pipeline reads the latest dated complete Vicmap WFS GeoJSON snapshot matching:

`data/raw/vicmap/foi_index_centroid_full_YYYY-MM-DD.geojson`

The latest snapshot is selected by the date in the filename, not by file modification time.

Dataset:
- Vicmap Features of Interest Index Centroid
- Source format: WFS GeoJSON
- Coordinate reference system: EPSG:4326
- Raw records: 106,084

The wrangling script does not call the WFS API directly. New snapshots are downloaded by `pipeline/acquisition/fetch_vicmap.py` before wrangling.

## Additional inputs

### LGA boundaries
data/raw/boundaries/vicmap_lga_2026-08-26.geojson
The boundary snapshot is used to spatially assign each Vicmap point to a local government area.
It is a fixed, versioned input committed to the repository and is not replaced during routine FOI refreshes.

### Subtype classification rules
data/validation/vicmap/vicmap_subtype_review.csv
This table maps every Vicmap feature_type and feature_subtype combination to:
- a classification decision;
- an activity category;
- a confidence basis; and
- classification notes.

### Product review rules
data/validation/vicmap/vicmap_product_review.csv
This table contains completed record-level review decisions, corrections, evidence URLs and review dates.

### Geographic scopes

#### Greater Melbourne master scope
The reusable master dataset covers 31 metropolitan councils.
This scope is retained to support future changes to the product area without repeating the complete statewide wrangling process.

#### Product scope
The current product outputs are limited to:
- City of Melbourne
- City of Melton
- City of Monash
Product-specific review and exclusion rules are applied only after the Greater Melbourne master outputs have been prepared.

## Processing workflow

### 1. Load and validate inputs
The script loads:
- the raw Vicmap GeoJSON snapshot;
- subtype classification rules;
- LGA boundary polygons; and
- completed product review decisions.
It validates required columns, boundary coverage, permitted decision values, rule uniqueness and review-table structure.

### 2. Standardise source records
The script creates a standardised base table by:
- normalising feature type and subtype text;
- preferring name_label over name;
- converting coordinates to numeric longitude and latitude;
- creating a stable place_id;
- preserving the original source record ID; and
- recording the source dataset and name provenance.
Generated place IDs follow this format:
vicmap_foi_<feature_id>

### 3. Filter to Greater Melbourne
Vicmap coordinates are converted into spatial points and joined to the official LGA boundary snapshot.
Only records located inside the configured 31 Greater Melbourne councils are retained.
The current Greater Melbourne scope contains 43,805 final processed records after reviewed deduplication.

### 4. Apply subtype classification rules
Each feature type and subtype is assigned one of four decisions:
- include
- exclude
- fallback
- review
Included records are mapped to one of seven activity categories:
- playground
- park_and_garden
- sports_ground
- court
- trail_access
- skate_bmx
- picnic_day_use
Every source subtype must match exactly one classification rule.

### 5. Review potential duplicates
Potential duplicates are identified using shared coordinates and feature subtypes.
Candidate records are exported to:
data/validation/vicmap/vicmap_potential_duplicates.csv
Completed duplicate decisions are reapplied when the script runs again.
The master dataset retains approved distinct records and removes only duplicates resolved by the review workflow.

### 6. Create display names
Official Vicmap names are retained whenever available.
The script uses the following name priority:
1. name_label
2. name
3. generated fallback label
When both source name fields are missing, a label is generated using the subtype and council, for example:
Unnamed Playground - Monash
Generated names are marked with:
name_source = generated_fallback
This prevents generated labels from being treated as official place names.

### 7. Create the product subset
After the Greater Melbourne processing is complete, records from Melbourne, Melton and Monash are selected for the product outputs.
The following deterministic product rules are then applied:
- named club sport facilities are moved to fallback;
- clear linear non-destination features, such as walkways and streetscapes, are removed from product outputs;
- clear same-location duplicates are collapsed;
- harmless display-name formatting is standardised; and
- completed record-level review decisions are applied.
These product rules do not modify the Greater Melbourne master outputs.

### 8. Apply formal review decisions
The following decisions are supported:
- keep
- keep_preferred
- move_to_fallback
- remove_duplicate
- exclude
The review table may also provide:
- a corrected display name;
- a corrected activity category;
- an evidence URL;
- review notes; and
- the date checked.
If a reviewed record is no longer present after a future source-data refresh, the rule remains in the review table for audit purposes.

### 9. Export and verify processed data
Every exported CSV is reopened and checked for:
- expected row count;
- unique place IDs; and
- successful file creation.
CSV files use UTF-8 with BOM for compatibility with Excel and other tools.

## Processed outputs
All processed Vicmap files are written to:
data/processed/vicmap/

### Greater Melbourne outputs

#### vicmap_places_greater_melbourne.csv
Complete processed master table containing all final classification decisions.
Current records: 43,805
This is primarily an audit and reusable scope dataset.

#### vicmap_recommendable_greater_melbourne.csv
Records classified as recommendable across the 31 Greater Melbourne councils.
Current records: 24,378

#### vicmap_fallback_greater_melbourne.csv
Greater Melbourne records classified as potentially useful but subject to possible access, fee, booking or operating-condition restrictions.
Current records: 478

### Product outputs

#### vicmap_app_ready.csv
The main application-facing recommendation dataset for Melbourne, Melton and Monash.
Current records: 2,859
These records passed the classification, geographic, duplicate and product-review rules.

#### vicmap_fallback.csv
Potentially useful product-scope records that should not be treated as unrestricted recommendations.
Current records: 101
The application may use these records through explicit fallback behaviour or additional access checks.

## Output columns
The application-facing outputs include:
- place_id
- display_name
- place_name
- name_source
- activity_category
- classification_confidence
- lga_name
- longitude
- latitude
- feature_type
- feature_subtype
- decision
- source_dataset
- source_record_id

## Relationship to validation
After wrangling, run:
python pipeline/validation/validate_vicmap.py
The validation workflow checks:
- output structure;
- product rules;
- spatial council assignments;
- application of formal review decisions;
- unresolved risk candidates; and
- a reproducible QA sample.
See:
pipeline/validation/README.md

## Reproducibility
The wrangling pipeline should be rerun whenever:
- a new Vicmap source snapshot is downloaded;
- the LGA boundary snapshot changes;
- subtype classification rules are updated;
- product review decisions are added;
- the product council scope changes; or
- product filtering policies are modified.
For a future API refresh:
1. run `python pipeline/run_vicmap_pipeline.py --refresh`;
2. inspect any new or stale review records or candidates;
3. rerun the pipeline after resolving any blocking issues; and
4. publish the outputs only after validation succeeds.

Individual acquisition, wrangling and validation scripts may still be run separately when diagnosing a failed stage.
