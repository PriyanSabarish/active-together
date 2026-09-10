# City of Melbourne Name Enrichment Validation

## Purpose

`validate_melbourne_names.py` checks the staged Melbourne-enriched dataset
against the Iteration 1 baseline and the same fixed City of Melbourne snapshots
used during wrangling. It does not modify any input.

## Inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/processed/name_enrichment/vicmap_app_ready_melbourne_enriched.csv
data/raw/melbourne/city_of_melbourne_playgrounds_2026-09-10.geojson
data/raw/melbourne/city_of_melbourne_landmarks_2026-09-10.geojson
```

## Run

```text
python pipeline/validation/validate_melbourne_names.py
```

## Checks

The script confirms that:

1. the baseline and staged files both contain 3,237 records;
2. columns and unique `place_id` values remain unchanged;
3. all non-name fields remain identical;
4. exactly eight approved Melbourne records receive official names;
5. each output name and source equals the reviewed decision;
6. the other 19 Melbourne targets retain generated names;
7. each accepted official name exists in the fixed source snapshot; and
8. the reviewed containment and maximum-distance conditions still hold.

## Expected result

```text
Melbourne enriched dataset validation passed.
Target locations: 27
Names updated: 8
Generated names retained: 19
Total output records: 3,237
```

Passing this validation approves the Melbourne stage for later consolidation.
It does not overwrite the official app-ready CSV before Melton is completed.
