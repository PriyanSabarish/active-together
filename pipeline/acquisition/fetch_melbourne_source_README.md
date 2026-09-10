# City of Melbourne Source Acquisition

## Purpose

`fetch_melbourne_source.py` downloads the two official sources used for the
Iteration 2 Melbourne name-enrichment work. It performs acquisition only and
does not match or update Vicmap names.

The routine pipeline uses fixed snapshots so that the manually reviewed result
remains reproducible. This script is therefore run only for an intentional
source refresh.

## Sources

- City of Melbourne `Playgrounds` dataset
- City of Melbourne `Landmarks and Places of Interest` dataset
- Provider: City of Melbourne Open Data Portal
- Licence: CC BY
- Output coordinate system: EPSG:4326

## Optional manual acquisition

From the project root, run:

```text
python pipeline/acquisition/fetch_melbourne_source.py
```

The script saves two dated GeoJSON snapshots and one metadata file under:

```text
data/raw/melbourne/
```

Existing same-day snapshots are not overwritten.

## Refresh policy

Acquisition is not part of the routine processing workflow. A replacement
snapshot must first be explored, and all manually approved matches must be
reviewed again. The fixed paths in the wrangling and validation scripts should
then be deliberately updated.
