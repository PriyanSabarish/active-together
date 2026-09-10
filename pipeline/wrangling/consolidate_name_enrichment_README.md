# Name Enrichment Consolidation

## Purpose

`consolidate_name_enrichment.py` combines the independently validated Monash,
Melbourne and Melton staged outputs into one complete name-enriched candidate.
It does not overwrite the Iteration 1 Vicmap baseline or the application
delivery CSV.

## Inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/processed/name_enrichment/vicmap_app_ready_monash_enriched.csv
data/processed/name_enrichment/vicmap_app_ready_melbourne_enriched.csv
data/processed/name_enrichment/vicmap_app_ready_melton_enriched.csv
```

Each staged input is a complete 3,237-row dataset containing changes for only
one council. The files must not be copied over one another.

## Run

```text
python pipeline/wrangling/consolidate_name_enrichment.py
```

## Checks and processing

The script confirms that every staged file retains the baseline structure and
non-name fields. It extracts only `display_name`, `place_name` and
`name_source` changes, verifies that the three council update sets do not
overlap, and applies their union to the baseline.

## Expected result

```text
Monash names included: 491
Melbourne names included: 8
Melton names included: 18
Total names updated: 517
Generated names retained: 186
Total output records: 3,237
```

## Output

```text
data/processed/name_enrichment/vicmap_app_ready_name_enriched.csv
```

This candidate must pass `validate_name_enrichment.py` before publication.
