# Melton Name Enrichment Wrangling

## Purpose

`wrangle_melton_names.py` applies the 18 Melton City Council names approved
during Iteration 2 exploration. It creates a staged complete dataset and does
not overwrite the official app-ready CSV.

## Fixed inputs

```text
data/processed/vicmap/vicmap_app_ready.csv
data/raw/melton/melton_open_space_2026-09-10.geojson
data/raw/melton/melton_ovals_and_fields_2026-09-10.geojson
```

The raw paths and approved `place_id` rules are intentionally fixed. Routine
wrangling does not fetch new source data or choose names using a general
nearest-distance rule.

## Run

```text
python pipeline/wrangling/wrangle_melton_names.py
```

## Process

The script:

1. selects the 111 Melton records with generated names;
2. corrects the known CRS metadata issue in both official snapshots;
3. recreates the 18 matches approved during exploration;
4. confirms each official source record and reviewed distance limit;
5. changes only `display_name`, `place_name` and `name_source`; and
6. saves one staged complete CSV.

Seventeen names come from `Melton Open Space`. One manually confirmed football
ground name comes from `Melton Ovals and Fields`. Google Maps names are not
used.

## Expected result

```text
Melton generated-name targets: 111
Names updated: 18
Generated names retained: 93
Total output records: 3,237
```

## Output

```text
data/processed/name_enrichment/vicmap_app_ready_melton_enriched.csv
```

The output must pass `validate_melton_names.py` before later consolidation with
the independently staged Monash and Melbourne results.
