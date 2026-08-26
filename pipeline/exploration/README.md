#

# Data Exploration

This directory contains exploratory notebooks used to understand project data sources before formal wrangling and integration.

Exploration notebooks are used for schema inspection, missing-value analysis, category review and data-quality assessment. They do not modify the original raw data.

## Notebooks

### Vicmap FOI

Notebook:

```text
vicmap_exploration.ipynb
```

### Source:
Vicmap Features of Interest Index Centroid WFS

### WFS layer:
open-data-platform:foi_index_centroid

### Raw snapshot:
data/raw/vicmap/foi_index_centroid_full_2026-08-26.geojson

The raw snapshot is downloaded through the WFS API and is not committed to GitHub.

## Vicmap exploration workflow
The Vicmap exploration followed these steps:
1. Download the complete WFS dataset using pagination.
2. Load and inspect the GeoJSON structure.
3. Review fields, missing values and coordinate coverage.
4. Analyse feature_type and feature_subtype distributions.
5. Create a subtype-level review table.
6. Define seven clear activity categories.
7. Apply high-confidence include and exclude rules.
8. Identify unverified fallback facilities.
9. Retain ambiguous subtypes for further review.
10. Export the subtype review table for later wrangling.

## Key findings
- Records: 106,084
- Feature types: 30
- Feature subtypes: 180
- Geometry: Point
- CRS: EPSG:4326
- Missing coordinates: 0
- Duplicate feature_id values: 0
- Missing name_label: approximately 46.4%
The dataset contains both suitable activity locations and many unrelated facilities. Classification must therefore operate primarily at the subtype level.


## Activity categories
The initial seven activity categories are:
- playground
- park_and_garden
- sports_ground
- court
- trail_access
- skate_bmx
- picnic_day_use

## Current classification outcome

| Decision  | Subtypes | Records  |
|---|---|
| Include   | 17       | 44,369   |
| Exclude   | 148      | 57,258   |
| Fallback  | 8        | 1,519    |
| Review    | 7        | 2,938    |
The seven remaining review subtypes require name-level classification, access verification or supporting spatial data.

## Exploration output

The subtype review table is stored at:
data/validation/vicmap/vicmap_subtype_review.csv
This table will be used as an input to the formal Vicmap wrangling pipeline.

## Scope note
The current working geographic scope is Greater Melbourne. The final scope may later be narrowed to selected local government areas. Geographic filtering will remain configurable so the wrangling process does not need to be redesigned.





