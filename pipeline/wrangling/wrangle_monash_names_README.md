# Monash Name Enrichment Wrangling

## Purpose

`wrangle_monash_names.py` enriches generated Monash location names using the
fixed VPA Draft Open Space snapshot selected during Iteration 2 exploration.
It produces a staged dataset and does not overwrite the official app-ready CSV.

## Fixed inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/raw/monash/vpa_open_space_monash_2026-09-10.geojson
```

The VPA path is intentionally fixed. The routine pipeline does not fetch the
source or automatically select a newer file.

## Run

```text
python pipeline/wrangling/wrangle_monash_names.py
```

## Process

The script:

1. selects Monash records with `name_source = generated_from_subtype`;
2. cleans whitespace and invalid VPA name values;
3. keeps named Monash VPA polygons;
4. matches each Vicmap point to its containing polygon;
5. rejects points matching multiple named polygons;
6. applies matched VPA names to a copy of the complete dataset; and
7. saves one staged CSV.

Only `display_name`, `place_name` and `name_source` are changed. The source name
describes the containing open space and does not necessarily represent a
separately named court or playground.

## Result

```text
Monash generated-name targets: 565
Names updated from VPA: 491
Generated names retained: 74
Total output records: 3,237
```

## Output

```text
data/processed/name_enrichment/vicmap_app_ready_monash_enriched.csv
```

The candidate mapping remains in memory and is not written as another CSV. The
staged output must pass `validate_monash_names.py` before final consolidation
with Melbourne and Melton.
