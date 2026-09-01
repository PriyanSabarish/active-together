# Vicmap Data Pipeline

This pipeline creates the location CSV used by Active Together for Melbourne,
Melton and Monash.

## Workflow

```text
Vicmap WFS API
      ↓
acquisition/fetch_vicmap.py
      ↓
dated raw GeoJSON snapshot
      ↓
wrangling/wrangle_vicmap.py
      ↓
data/processed/vicmap/vicmap_app_ready.csv
      ↓
validation/validate_vicmap.py
```

The fixed LGA boundary file and the subtype classification table are supporting
inputs. Exploration notebooks and QA files help explain decisions but are not
application inputs.

The classification table retains all historical exploration decisions, but the
current production workflow uses only rows marked `include`.

## Run with an existing snapshot

From the project root:

```powershell
python pipeline/run_vicmap_pipeline.py
```

This runs wrangling followed by validation. The newest dated complete snapshot
in `data/raw/vicmap/` is selected automatically.

## Download and process fresh Vicmap data

```powershell
python pipeline/run_vicmap_pipeline.py --refresh
```

This runs acquisition, wrangling and validation. The default WFS page size is
5,000 records.

## Stages

### Acquisition

Downloads the complete Vicmap WFS layer and saves a dated raw snapshot. Existing
same-day snapshots are not overwritten.

### Wrangling

Keeps records with a usable ID, subtype and valid coordinates; applies the
approved subtype categories; limits records to Melbourne, Melton and Monash;
creates deterministic labels where Vicmap names are missing; removes exact
coordinate-subtype duplicates; and writes one app-ready CSV.

### Validation

Checks the CSV structure, required values, unique IDs, coordinates, categories,
generated-name rules, coordinate-subtype duplicates, council coverage and
spatial boundaries. Validation reports errors but does not change product data.

## Product output

Application developers should use only:

```text
data/processed/vicmap/vicmap_app_ready.csv
```

The raw Vicmap snapshots are excluded from GitHub. The fixed boundary file,
scripts, classification rules and app-ready CSV are versioned so the workflow
can be understood and reproduced.

## More information

- [Acquisition](acquisition/README.md)
- [Exploration](exploration/README.md)
- [Wrangling](wrangling/README.md)
- [Validation](validation/README.md)
