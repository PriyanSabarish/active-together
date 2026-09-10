# Data Exploration

## Purpose

The exploration notebooks document how the Vicmap location data was examined before reproducible cleaning and validation rules were applied.

Exploration is kept separate from processing. The notebooks do not overwrite the raw data or the application-ready dataset.

## Notebooks

```text
pipeline/exploration/vicmap_exploration.ipynb
pipeline/exploration/01_monash_unnamed_exploration.ipynb
```

## Iteration 1: Vicmap exploration

The first notebook explored the statewide Vicmap Features of Interest dataset. It examined the source structure, coordinates, identifiers, missing names and feature subtypes.

Relevant subtypes were classified into seven activity-location categories:

- `playground`
- `park_and_garden`
- `sports_ground`
- `court`
- `trail_access`
- `skate_bmx`
- `picnic_day_use`

The resulting classification rules were used to produce the application-ready dataset containing 3,237 locations across Melbourne, Melton and Monash.

## Iteration 2: Monash name exploration

The second notebook investigated whether externally sourced names could replace the generated names used during Iteration 1.

The application-ready CSV contained 703 generated names, including 565 in Monash. Two external sources were explored.

### VPA Open Space

Named VPA open-space polygons were spatially matched to the Monash target points. This produced candidate names for 491 of the 565 locations, giving 86.9% coverage.

These candidates proceed to the cleaning and validation stages before any values are replaced. Because the VPA dataset is no longer actively maintained, the explored `2026-09-10` snapshot is fixed as the reproducible Iteration 2 input. The routine pipeline does not fetch VPA again on every run.

### OpenStreetMap

OpenStreetMap recreation features were retrieved through the Overpass API and compared with the 565 target locations.

Using a conservative 50-metre threshold:

- 233 locations had an OSM candidate;
- 226 were already covered by VPA;
- only 7 were additional OSM-only candidates;
- 5 were direct park candidates; and
- 2 were contextual names rather than names of the target facilities.

Because OSM added little coverage and some matches represented a surrounding park, school or community space rather than the target feature, OSM was not selected for automated name replacement.

## Exploration result

The source decision from this exploration is:

- continue with the 491 VPA candidate names;
- clean and validate the VPA candidates before replacement;
- retain the 74 Iteration 1 generated names without a reliable VPA match; and
- retain OSM only as exploratory and comparison evidence.

This approach avoids assigning unsupported nearby or parent-place names to more specific Vicmap features.

## Sources

- Vicmap Features of Interest
- VPA Draft Open Space Data
- [OpenStreetMap](https://www.openstreetmap.org/copyright), accessed through the Overpass API
