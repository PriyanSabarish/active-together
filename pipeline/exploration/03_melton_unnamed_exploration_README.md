# Melton Name Enrichment Exploration

## Purpose

`03_melton_unnamed_exploration.ipynb` assesses whether official Melton City
Council data can replace generated names for the 111 Melton targets left by
Iteration 1. The notebook records exploration and review decisions only.

## Target population

- 20 courts
- 52 parks and gardens
- 39 sports grounds or complexes
- 111 targets in total

All targets had unique IDs and complete coordinates.

## Sources explored

- `Melton Open Space`
- `Melton Recreation Facilities`
- `Melton Ovals and Fields`
- `Melton Netball Courts`
- `Melton Tennis Courts`
- `Melton Basketball Courts`
- Google Maps for manual visual confirmation only

The official GeoJSON responses label their geometry as EPSG:4326 even though
their coordinates use MGA Zone 55 (EPSG:28355). Exploration corrected this
metadata before spatial comparison.

## Findings

The Open Space source produced 17 candidates within 50 metres. These were
manually reviewed and accepted. Wider distance thresholds were not adopted.

The general Recreation Facilities source produced no candidates within 100
metres. The netball and tennis sources produced no candidates within 200
metres, and the basketball GeoJSON contained no records. These sources did not
contribute a final name.

The Ovals and Fields source produced two candidates within 100 metres. Manual
map review confirmed the Kurunjang football-ground candidate and rejected the
Eynesbury candidate because its target point lay on an unconfirmed open area.
Google Maps names were not copied into the data.

## Result

- 17 Open Space names accepted
- 1 Ovals and Fields name accepted
- 18 official names accepted in total
- 93 generated names retained

The accepted decisions are explicit `place_id` rules. Proximity alone is not a
production name-assignment rule.

## Reproducibility decision

Only the two sources that contributed accepted names are retained as fixed
`2026-09-10` snapshots:

```text
data/raw/melton/melton_open_space_2026-09-10.geojson
data/raw/melton/melton_ovals_and_fields_2026-09-10.geojson
```

Acquisition is optional and is not part of the routine pipeline. Any source
refresh requires a new exploration and manual review.

## Next stages

```text
pipeline/wrangling/wrangle_melton_names.py
pipeline/validation/validate_melton_names.py
```
