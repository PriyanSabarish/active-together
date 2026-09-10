# Monash Name Enrichment Validation

## Purpose

`validate_monash_names.py` validates the staged Monash-enriched dataset against
the Iteration 1 baseline and the same fixed VPA snapshot used by wrangling. It
does not modify either dataset.

## Inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/processed/name_enrichment/vicmap_app_ready_monash_enriched.csv
data/raw/monash/vpa_open_space_monash_2026-09-10.geojson
```

## Run

```text
python pipeline/validation/validate_monash_names.py
```

## Checks

The script confirms that:

1. both complete datasets contain 3,237 records;
2. columns and unique `place_id` values remain unchanged;
3. all non-name fields are identical to the baseline;
4. exactly 491 intended Monash records received VPA names;
5. updated names are clean and use `name_source = vpa_open_space`;
6. 74 unmatched Monash records retain their generated names;
7. every updated point lies within a named polygon in the fixed VPA snapshot;
8. every applied name equals the cleaned source polygon name; and
9. no point has multiple named polygon matches.

## Expected result

```text
Monash enriched dataset validation passed.
Target locations: 565
Names updated: 491
Generated names retained: 74
Total output records: 3,237
```

Passing this validation approves the Monash stage for later consolidation. It
does not replace the official app-ready CSV before Melbourne and Melton have
completed their own enrichment and validation stages.
