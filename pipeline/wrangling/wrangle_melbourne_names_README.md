# City of Melbourne Name Enrichment Wrangling

## Purpose

`wrangle_melbourne_names.py` applies the eight City of Melbourne names approved
during Iteration 2 exploration. It creates a staged complete dataset and does
not overwrite the official app-ready CSV.

## Fixed inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/raw/melbourne/city_of_melbourne_playgrounds_2026-09-10.geojson
data/raw/melbourne/city_of_melbourne_landmarks_2026-09-10.geojson
```

The raw paths are intentionally fixed. Routine wrangling does not fetch or
automatically select newer source files.

## Run

```text
python pipeline/wrangling/wrangle_melbourne_names.py
```

## Process

The script:

1. selects the 27 Melbourne records with generated names;
2. cleans official playground and landmark names;
3. recreates the eight matches accepted during exploration;
4. checks the reviewed containment or maximum distance for every match;
5. changes only `display_name`, `place_name` and `name_source`; and
6. saves one staged complete CSV.

Three playground matches use polygon containment. One additional playground
and four landmark matches were accepted after manual spatial review. Google
Maps names are not used.

## Expected result

```text
Melbourne generated-name targets: 27
Names updated: 8
Generated names retained: 19
Total output records: 3,237
```

## Output

```text
data/processed/name_enrichment/vicmap_app_ready_melbourne_enriched.csv
```

The output must pass `validate_melbourne_names.py` before later consolidation
with the independently staged Monash and Melton results.
