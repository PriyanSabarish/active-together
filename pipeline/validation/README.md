# Vicmap Validation

## Purpose

`validate_vicmap.py` checks whether the processed Vicmap CSV is safe to pass to
the application. It reports errors but does not add, remove or edit any place.

Vicmap remains the source of truth. Manual QA and external websites may be used
to discuss data limitations, but they do not change this validation result.

## Input

The script reads:

- `data/processed/vicmap/vicmap_app_ready.csv`
- `data/raw/boundaries/vicmap_lga_2026-08-26.geojson`

## Checks

The script confirms that:

- all 14 required columns are present;
- required values are not missing or blank;
- `place_id` values are unique;
- longitude and latitude are numeric and valid;
- every record has `decision = include`;
- every record identifies `vicmap_foi` as its source;
- only the seven approved activity categories are used;
- Melbourne, Melton and Monash are all represented; and
- each place falls inside its stated council boundary.

The seven activity categories are:

- `playground`
- `park_and_garden`
- `sports_ground`
- `court`
- `trail_access`
- `skate_bmx`
- `picnic_day_use`

## Run the validation

From the project root:

```powershell
python pipeline/validation/validate_vicmap.py
```

To run wrangling and validation together:

```powershell
python pipeline/run_vicmap_pipeline.py
```

A successful run ends with:

```text
Vicmap validation completed successfully.
```

## Current result

The current app-ready file contains 2,585 named places across Melbourne,
Melton and Monash. It contains no missing required values or duplicate place
IDs and passes all category, coordinate and spatial checks.

## QA note

QA samples and earlier review tables are supporting analysis files only. They
can be used to describe known Vicmap limitations, but they are not application
inputs and are not used to rewrite the app-ready CSV.
