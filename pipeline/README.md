# Data Pipeline

This directory contains the reproducible data-processing workflows for Active Together.

The current automated workflow covers the Vicmap Features of Interest dataset and produces product-facing location data for Melbourne, Melton and Monash.

## Current workflow

```text
Vicmap WFS API
      ↓
acquisition/fetch_vicmap.py
      ↓
data/raw/vicmap/foi_index_centroid_full_YYYY-MM-DD.geojson
      ├──────────────┐
fixed LGA boundary ─┤
review rules ───────┤
                    ↓
       wrangling/wrangle_vicmap.py
                    ↓
data/processed/vicmap/vicmap_app_ready.csv
data/processed/vicmap/vicmap_fallback.csv
                    ↓
validation/validate_vicmap.py
```

Exploration notebooks and notes support rule development but are not executed by the automated refresh workflow.

## Unified runner

Run commands from the project root.

### Process the latest existing snapshot

```powershell
python pipeline/run_vicmap_pipeline.py
```

This runs:

```text
wrangling → validation
```

The wrangling script automatically selects the complete raw snapshot with the latest date in its filename.

### Download and process a new snapshot

```powershell
python pipeline/run_vicmap_pipeline.py --refresh
```

This runs:

```text
acquisition → wrangling → validation
```

The WFS page size can be changed only when needed for API troubleshooting:

```powershell
python pipeline/run_vicmap_pipeline.py --refresh --page-size 2000
```

The default page size is 5,000 records.

## Pipeline stages

### Acquisition

Downloads the Vicmap WFS layer in pages, validates the complete response and saves a dated raw GeoJSON snapshot with metadata and a SHA-256 checksum.

Existing same-day snapshots are not overwritten.

The LGA boundary is a fixed, versioned pipeline input and is not replaced during routine FOI acquisition.

### Wrangling

Standardises source records, assigns Greater Melbourne councils, applies subtype classification and duplicate decisions, creates display names, applies product-scope review rules, and exports the processed datasets.

Greater Melbourne master outputs are retained locally, while the product outputs are limited to Melbourne, Melton and Monash.

### Validation

Checks table structure, product decisions, category values, council assignments, coordinates and completed review decisions. It also generates QA samples and unresolved review candidates.

Validation checks the processed outputs; it does not modify the app-ready or fallback data.

## Product outputs

Application developers should use:

```text
data/processed/vicmap/vicmap_app_ready.csv
data/processed/vicmap/vicmap_fallback.csv
```

See `data/README.md` for column descriptions and usage guidance.

## Failure behaviour

Each stage stops with an error when a required check fails. The unified runner does not continue to later stages after a failure.

New processed data should be shared with the application only when the complete validation stage succeeds.

Raw FOI snapshots are excluded from GitHub and remain in `data/raw/` according to the project data management rules. The fixed LGA boundary is committed because it is required to reproduce council assignments.

## Documentation

- [Data acquisition](acquisition/README.md)
- [Data exploration](exploration/README.md)
- [Data wrangling](wrangling/README.md)
- [Data validation](validation/README.md)

