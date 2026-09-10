# Melton City Council Source Acquisition

## Purpose

`fetch_melton_source.py` downloads the two official sources that support the
reviewed Melton name-enrichment decisions. It performs acquisition only and
does not match or update Vicmap names.

The routine workflow uses fixed snapshots so the manually reviewed results
remain reproducible. This script is run only for an intentional source refresh.

## Sources

- `Melton Open Space`
- `Melton Ovals and Fields`
- Provider: Melton City Council via data.gov.au
- Licence: Creative Commons Attribution 2.5 Australia
- Actual source coordinate system: EPSG:28355

The GeoJSON responses label their geometry as EPSG:4326 even though the stored
coordinates use MGA Zone 55 (EPSG:28355). The raw responses are preserved
unchanged, and the wrangling and validation scripts explicitly correct this
metadata before transforming the geometry.

## Optional manual acquisition

From the project root, run:

```text
python pipeline/acquisition/fetch_melton_source.py
```

The script saves two dated GeoJSON snapshots and one metadata file under:

```text
data/raw/melton/
```

Existing same-day snapshots are not overwritten.

## Refresh policy

Acquisition is not part of the routine processing workflow. A replacement
snapshot must first be explored, and all manually approved matches must be
reviewed again. The fixed paths and approved rules in the wrangling and
validation scripts must then be deliberately updated.

The general recreation, netball, tennis and basketball datasets explored in
the notebook did not contribute a final accepted name, so they are not
production inputs and are not downloaded by this script.
