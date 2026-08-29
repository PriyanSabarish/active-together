# Vicmap Wrangling

## Purpose

`wrangle_vicmap.py` converts the latest raw Vicmap snapshot into the location
CSV used by Active Together.

Vicmap is treated as the source of truth. The script does not search external
websites, manually correct individual records or create fallback places.

## Inputs

The script reads:

- the latest `data/raw/vicmap/foi_index_centroid_full_YYYY-MM-DD.geojson`;
- `data/validation/vicmap/vicmap_subtype_review.csv`; and
- `data/raw/boundaries/vicmap_lga_2026-08-26.geojson`.

The subtype review table supplies the approved mapping from Vicmap subtypes to
the seven product activity categories.

## Processing steps

The script:

1. loads the newest complete Vicmap snapshot;
2. keeps the source fields required by the product;
3. removes records without a usable ID, subtype or valid coordinates;
4. keeps only subtypes marked `include` in the classification table;
5. assigns locations to council boundaries;
6. keeps Melbourne, Melton and Monash; and
7. keeps one record for each subtype at the same coordinates;
8. creates a deterministic label when Vicmap has no name; and
9. exports a stable 14-column CSV.

Generated labels follow this format:

```text
Unnamed {Feature Subtype} - {Council} - {Source Record ID}
```

They are marked with `name_source = generated_from_subtype` and do not represent
official facility names.

## Activity categories

- `playground`
- `park_and_garden`
- `sports_ground`
- `court`
- `trail_access`
- `skate_bmx`
- `picnic_day_use`

## Output

```text
data/processed/vicmap/vicmap_app_ready.csv
```

This is the only Vicmap location table intended for the application. Each row
represents one source location and contains its display label, category,
council, coordinates, source subtype and traceable Vicmap identifier.

## Run the script

From the project root:

```powershell
python pipeline/wrangling/wrangle_vicmap.py
```

The output must pass:

```powershell
python pipeline/validation/validate_vicmap.py
```

For the normal combined workflow, use:

```powershell
python pipeline/run_vicmap_pipeline.py
```

## QA note

Exploration and QA files document source-data limitations and classification
decisions. They do not directly edit or override the app-ready records.
