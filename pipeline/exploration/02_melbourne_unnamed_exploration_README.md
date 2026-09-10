# City of Melbourne Name Enrichment Exploration

## Purpose

`02_melbourne_unnamed_exploration.ipynb` assesses whether official City of
Melbourne data can replace generated names for the 27 Melbourne targets left
by Iteration 1. The notebook is exploratory and does not overwrite application
data.

## Sources

- City of Melbourne `Playgrounds`
- City of Melbourne `Landmarks and Places of Interest`
- Google Maps for manual visual confirmation only

Google Maps names were not copied into the dataset.

## Method

Named playground polygons were tested using point containment and short
nearest distances. Relevant recreation landmarks were matched by distance.
Candidates without a direct spatial relationship were manually reviewed before
being accepted or rejected.

## Result

- 27 generated-name targets assessed
- 4 official playground names accepted
- 4 official landmark names accepted
- 19 generated names retained

The eight accepted decisions are implemented as explicit rules rather than a
general distance threshold.

## Reproducibility decision

The two official sources are stored as fixed `2026-09-10` snapshots. Routine
wrangling does not fetch updated source data because new geometries or names
would require the candidates to be explored and manually reviewed again.

## Next stages

```text
pipeline/wrangling/wrangle_melbourne_names.py
pipeline/validation/validate_melbourne_names.py
```
