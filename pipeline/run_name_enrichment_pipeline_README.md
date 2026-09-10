# Iteration 2 Name Enrichment Pipeline

## Purpose

`run_name_enrichment_pipeline.py` runs the complete reviewed council
name-enrichment workflow for Monash, Melbourne and Melton.

It is separate from the Iteration 1 Vicmap pipeline because the enrichment
rules use fixed council snapshots and manually approved matches. The runner
does not download or refresh source data.

## Default run

From the project root, run:

```text
python pipeline/run_name_enrichment_pipeline.py
```

The default mode:

1. runs Monash wrangling and validation;
2. runs Melbourne wrangling and validation;
3. runs Melton wrangling and validation;
4. consolidates the three staged outputs; and
5. validates the consolidated candidate.

It creates or refreshes:

```text
data/processed/name_enrichment/vicmap_app_ready_name_enriched.csv
```

The default mode does not modify the published application CSV.

## Validate and publish

To publish only after every stage passes, run:

```text
python pipeline/run_name_enrichment_pipeline.py --publish
```

The final validation step then atomically replaces:

```text
data/vicmap_app_ready.csv
```

The pre-enrichment baseline remains unchanged at:

```text
data/processed/vicmap/vicmap_app_ready.csv
```

## Expected result

```text
Monash names: 491
Melbourne names: 8
Melton names: 18
Total names updated: 517
Generated names retained: 186
Total output records: 3,237
```

## Failure behaviour

The runner executes each stage in order and stops immediately if any script
fails. Publication cannot occur unless all three council validations,
consolidation and final validation succeed.

If Iteration 1 produces a newer Vicmap baseline with changed IDs, coordinates
or target counts, the enrichment workflow may stop. The affected council
matches must then be explored and reviewed again before its fixed rules are
updated.

## Source refresh policy

Council acquisition scripts remain optional standalone utilities. A refreshed
snapshot must never enter this workflow until exploration and manual review
have approved the resulting matches.
