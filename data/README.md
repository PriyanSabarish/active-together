# Data Guide

## Start here

This page explains which Vicmap files other team members should use.

The current product covers:

- Melbourne
- Melton
- Monash

## Application data

The application should use only:

```text
data/processed/vicmap/vicmap_app_ready.csv
```

This CSV contains Vicmap locations that:

- have a usable source ID, subtype and valid coordinates;
- match an approved activity subtype;
- are located inside one of the three selected councils; and
- passed the automated validation checks.

The current file contains 3,237 locations. It is a static application-ready
output that can be regenerated from a newer Vicmap API snapshot.

When Vicmap does not provide a name, the pipeline creates a deterministic label:

```text
Unnamed {Feature Subtype} - {Council} - {Source Record ID}
```

For example: `Unnamed Playground - Monash - 12345`. This is a location label,
not a claim that Vicmap supplied an official facility name.

## Activity categories

Each location has one of seven labels:

- `playground`
- `park_and_garden`
- `sports_ground`
- `court`
- `trail_access`
- `skate_bmx`
- `picnic_day_use`

These labels allow the future activity-template data to match an activity with
suitable types of locations.

## Output columns

| Column | Description |
|---|---|
| `place_id` | Stable application identifier |
| `display_name` | Source name or deterministic unnamed label shown to users |
| `place_name` | Cleaned source name or deterministic unnamed label |
| `name_source` | `vicmap_name`, `vicmap_name_label` or `generated_from_subtype` |
| `activity_category` | One of the seven location labels |
| `classification_confidence` | Confidence recorded in the subtype rule |
| `lga_name` | Melbourne, Melton or Monash |
| `longitude` | Longitude in EPSG:4326 |
| `latitude` | Latitude in EPSG:4326 |
| `feature_type` | Original Vicmap feature type |
| `feature_subtype` | Original Vicmap feature subtype |
| `decision` | Always `include` for this output |
| `source_dataset` | Always `vicmap_foi` |
| `source_record_id` | Original Vicmap feature ID |

## Supporting files

### Raw Vicmap snapshots

```text
data/raw/vicmap/
```

Raw GeoJSON snapshots and metadata remain local and are ignored by Git. They
are pipeline inputs, not application inputs.

### Council boundaries

```text
data/raw/boundaries/vicmap_lga_2026-08-26.geojson
```

This fixed boundary snapshot is committed because wrangling and validation need
it to reproduce the three-council scope.

### Classification rules

```text
data/validation/vicmap/vicmap_subtype_review.csv
```

This table records the exploration decisions for all Vicmap subtypes. The
current wrangling script uses only rows whose `decision` is `include`. Other
decision values remain as historical exploration information.

QA samples and review working files are supporting analysis only. They are not
loaded by the application and do not rewrite the app-ready CSV.

## Refresh the data

Use the newest existing local snapshot:

```powershell
python pipeline/run_vicmap_pipeline.py
```

Download a new Vicmap snapshot before processing:

```powershell
python pipeline/run_vicmap_pipeline.py --refresh
```

Only share a regenerated app-ready CSV after validation completes successfully.

## Technical documentation

- `pipeline/README.md`
- `pipeline/acquisition/README.md`
- `pipeline/exploration/README.md`
- `pipeline/wrangling/README.md`
- `pipeline/validation/README.md`

Most team members only need this guide and `vicmap_app_ready.csv`.
