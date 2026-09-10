# Melton Name Enrichment Validation

## Purpose

`validate_melton_names.py` checks the staged Melton-enriched dataset against
the Iteration 1 baseline and the same fixed Melton City Council snapshots used
during wrangling. It does not modify any input.

## Inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/processed/name_enrichment/vicmap_app_ready_melton_enriched.csv
data/raw/melton/melton_open_space_2026-09-10.geojson
data/raw/melton/melton_ovals_and_fields_2026-09-10.geojson
```

## Run

```text
python pipeline/validation/validate_melton_names.py
```

## Checks

The script confirms that:

1. the baseline and staged files both contain 3,237 records;
2. columns and unique `place_id` values remain unchanged;
3. all non-name fields remain identical;
4. exactly 18 approved Melton records receive official names;
5. each output name and source equals the reviewed decision;
6. the other 93 Melton targets retain generated names;
7. every accepted name and asset ID exists in the fixed source; and
8. every accepted feature remains within its reviewed distance limit.

## Expected result

```text
Melton enriched dataset validation passed.
Target locations: 111
Names updated: 18
Generated names retained: 93
Total output records: 3,237
```

Passing this validation approves the Melton stage for later consolidation. It
does not overwrite the official app-ready CSV.
