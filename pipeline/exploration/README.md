# Vicmap Data Exploration

## Purpose

The exploration notebook was used to understand the Vicmap Features of Interest
dataset before writing the reproducible pipeline. Exploration does not modify
the raw source data or the application-ready CSV.

## Notebook

```text
pipeline/exploration/vicmap_exploration.ipynb
```

The notebook records the analysis performed using the historical
`foi_index_centroid_full_2026-08-26.geojson` snapshot. Raw snapshots remain
local and are not committed to GitHub.

## Source

- Dataset: Vicmap Features of Interest Index Centroid
- WFS layer: `open-data-platform:foi_index_centroid`
- Geometry: Point
- Coordinate system: EPSG:4326

## Exploration process

The notebook:

1. inspected the GeoJSON structure and fields;
2. checked record counts, coordinates, IDs and missing names;
3. reviewed `feature_type` and `feature_subtype` values;
4. created an inventory of 180 subtypes;
5. defined seven activity-location categories; and
6. recorded subtype decisions in a reusable classification table.

## Key findings

- Records: 106,084
- Feature types: 30
- Feature subtypes: 180
- Missing coordinates: 0
- Duplicate `feature_id` values: 0
- Missing place names: approximately 46.4%

Vicmap contains both useful activity locations and many unrelated facilities.
Subtype classification is therefore required before geographic filtering.

## Seven location categories

- `playground`
- `park_and_garden`
- `sports_ground`
- `court`
- `trail_access`
- `skate_bmx`
- `picnic_day_use`

## Historical decision inventory

The exploration table contains four decision labels:

| Decision | Subtypes | Historical records |
|---|---:|---:|
| `include` | 17 | 44,369 |
| `exclude` | 148 | 57,258 |
| `fallback` | 8 | 1,519 |
| `review` | 7 | 2,938 |

These values describe the exploration stage. Under the simplified production
logic, `wrangle_vicmap.py` uses only the 17 `include` subtype rules. It does not
generate fallback data, apply name-level manual decisions or consult external
websites. The other labels remain only as an audit trail of the exploration.

## Exploration output

```text
data/validation/vicmap/vicmap_subtype_review.csv
```

This table is the classification input used by wrangling.

## Geographic scope

Exploration examined the complete statewide Vicmap snapshot so subtype rules
would not depend on one council. The current wrangling script then applies the
rules and keeps only locations inside Melbourne, Melton and Monash.

The current pipeline does not generate Greater Melbourne master outputs.
