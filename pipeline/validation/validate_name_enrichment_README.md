# Consolidated Name Enrichment Validation

## Purpose

`validate_name_enrichment.py` validates the consolidated name-enriched
candidate against the Iteration 1 baseline and all three council staged
outputs. Validation is read-only unless the explicit `--publish` option is
used.

## Validate

```text
python pipeline/validation/validate_name_enrichment.py
```

The script checks:

1. the 3,237-row structure and unique IDs are unchanged;
2. every non-name field remains identical to the baseline;
3. the final changes equal the exact union of the three staged files;
4. the three council update sets do not overlap;
5. 517 approved names are present;
6. 186 generated names remain; and
7. all changed names are non-empty and consistently stored.

## Publish after validation

```text
python pipeline/validation/validate_name_enrichment.py --publish
```

The command runs every validation check first. Only after they pass does it
atomically replace the application delivery file:

```text
data/vicmap_app_ready.csv
```

The Iteration 1 baseline remains unchanged at:

```text
data/processed/vicmap/vicmap_app_ready.csv
```

Keeping the baseline separate allows all council wrangling and validation
scripts to remain reproducible.
