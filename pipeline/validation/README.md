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
- each generated name follows the deterministic unnamed-label format;
- no subtype is repeated at exactly the same coordinates;
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

The current app-ready file contains 3,237 places across Melbourne, Melton and
Monash, including deterministic labels for 703 unnamed source records. It
contains no missing required values, duplicate place IDs or duplicate
coordinate-subtype rows and passes all naming, category and spatial checks.

## Classification QA sampling

`generate_vicmap_qa_sample.py` creates a reproducible sample for manual checks
of the Vicmap subtype-to-category classification. It is separate from the
normal pipeline and does not modify `vicmap_app_ready.csv`.

From the project root, run:

```powershell
python pipeline/validation/generate_vicmap_qa_sample.py
```

The script:

- reads the validated `vicmap_app_ready.csv` file;
- uses the fixed random seed `5120`;
- samples up to 30 records from each activity category;
- includes every record when a category contains fewer than 30 records; and
- refuses to overwrite an existing QA sample.

The current sample contains 152 records across all seven categories and is
saved as:

```text
data/validation/vicmap/vicmap_qa_sample.csv
```

### Review process

Two reviewers should assess the same sample independently. Each reviewer uses
only their own result, suggested-category and notes columns. Recommended result
values are `correct`, `incorrect` and `unsure`.

When both reviews are complete:

- matching decisions can be accepted directly;
- disagreements and `unsure` records require final resolution; and
- the agreed result can be saved as `vicmap_qa_results.csv`.

QA results measure classification quality. They do not automatically change
the application CSV. If QA identifies a systematic subtype-classification
problem, the team should review `vicmap_subtype_review.csv`, rerun wrangling
and validation, and document the rule change.

Earlier QA and product-review files belong to the retired record-level review
workflow and are not inputs to the current pipeline.
