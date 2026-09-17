# Server

FastAPI backend for Active Together.

## Structure

```
server/
  app/
    __init__.py
    models.py          Shared types — the A/B contract
  tests/
    __init__.py
    fixtures.py        Test data for recommendation logic
```

## The Backend A / B split

Backend work is divided into two roles with a defined interface between them.

| | Backend A | Backend B |
|---|---|---|
| Owns | Database, spatial queries, external services | Scoring, tiering, ordering, explanations |
| Talks to | PostGIS, Open-Meteo, the client | Backend A only |
| Testable with | A live database and network | Fixtures alone |

Backend B never queries the database or calls an external API directly.
Everything it needs arrives as a function argument, which is why it can be
built and tested before any infrastructure exists.

## `app/models.py` — the contract

This module defines every object that crosses between the two roles. **Both
sides import it. Neither side defines its own version of these types.**

### What Backend A produces

`Place` — a candidate location from `vicmap_app_ready.csv`.

| Field | Type | Note |
|---|---|---|
| `place_id` | `str` | |
| `display_name` | `str \| None` | Nullable — a share of FOI records have no usable name |
| `activity_category` | `ActivityCategory` | One of the seven pipeline categories |
| `lga_name` | `str` | |
| `latitude` / `longitude` | `float` | |
| `distance_m` | `int` | Straight-line metres, computed by A via `ST_Distance` |
| `classification_confidence` | `float` | 0.0 – 1.0 |

`Context` — environmental data for a location and time.

| Field | Type | Note |
|---|---|---|
| `available` | `bool` | `False` when the Open-Meteo call failed |
| `temp_c` | `float \| None` | |
| `precip_prob` | `float \| None` | 0.0 – 1.0 |
| `wind_gust_kmh` | `float \| None` | |
| `uv_index` | `float \| None` | |
| `pm25` / `pm10` | `float \| None` | Micrograms per cubic metre |

When the forecast call fails, A returns `Context(available=False)` with every
other field `None`. It does **not** raise. Story 2.2 requires candidates to
still be shown with the weather labelled unavailable, so the failure has to
arrive as a value.

### What Backend B produces

`Recommendation` — `status`, up to three `Combo` objects, and a `message` when
the status is `zero_results`.

`Combo` — a `Place` plus activity type, entered duration, matched bucket,
combo template, tier, `EnvironmentalSummary` and explanation.

`EnvironmentalSummary` mirrors `Context` but adds `warnings` and `reminders` as
derived fields. Threshold logic lives in Backend B only — the client renders
what it is given rather than re-implementing the 60% / 40 km/h rules in Vue.

### Fixed values

```python
ALLOWED_RADIUS_KM   = (3, 5, 10)
DURATION_MIN_BOUNDS = (20, 120)
DURATION_BUCKETS    = (20, 40, 60)
```

Seven categories: `playground`, `park_and_garden`, `sports_ground`, `court`,
`trail_access`, `skate_bmx`, `picnic_day_use`.

### Changing this file

A change here breaks the other side silently. Any change is a pull request
approved by **both** backend owners — not a message in chat.

## Iteration 2 — missions

`app/models.py` also carries `Mission` and `Step`, the shapes that cross the
wire on `POST /missions` and `POST /verify-step`. `AgeBand` and `VerifyMode`
live there too since both the wire shapes and the template schema below use
them.

`app/missions/models.py` is the frozen template **family** schema agreed
with Content — one Pydantic model per
`content/schema/mission_template.schema.yaml`. It enforces structure only
(required fields, types, and `prompt_id` being required when `verify_mode`
is `photo`). Cross-band and cross-template rules — step counts matching the
duration bucket, the 5-7 band's word limit, `prompt_id` membership in the
measured vocabulary — are the schema validator (B21) and safety validator
(B22), not this module.

`app/missions/loader.py` parses `content/missions/*.yaml` into
`MissionTemplate` objects, non-recursively (so drafts under `_candidates/`
are never loaded). A content author can check a draft file parses before
opening a pull request:

```python
from pathlib import Path
from app.missions.loader import load_template_file

load_template_file(Path("content/missions/playground.yaml"))
```

## `tests/fixtures.py` — test data

Lets recommendation logic be developed without PostGIS, without Open-Meteo, and
before Backend A's services exist.

### Place sets

| Name | Contents | Exercises |
|---|---|---|
| `DENSE_INNER` | 10 places, inner Melbourne, all 7 categories | Normal ranking |
| `MIDDLE_MONASH` | 4 places, Monash | Moderate density |
| `SPARSE_OUTER` | 2 places, Melton | Fewer-than-three path |
| `EMPTY` | none | Zero-result path |
| `LOW_CONFIDENCE` | 2 places below any sensible threshold | Suppression |
| `SINGLE_CATEGORY` | derived from `DENSE_INNER` | Preference filtering (iteration 2) |

Two places have `display_name=None` on purpose — `fx_006` and `fx_102`.

### Context values

Threshold reference:

| Condition | Threshold | Effect |
|---|---|---|
| Precipitation probability | ≥ 0.60 | Warning + deprioritised |
| Wind gusts | ≥ 40.0 km/h | Warning + deprioritised |
| PM2.5 | ≥ 25.0 | Warning + deprioritised |
| PM10 | ≥ 80.0 | Warning + deprioritised |
| UV index | ≥ 3.0 | Reminder only — **not** deprioritised |

Boundary fixtures exist in pairs so the comparison operator can be verified:
`RAIN_AT_THRESHOLD` is exactly 0.60 and `RAIN_BELOW_THRESHOLD` is 0.59.
`WIND_AT_THRESHOLD` is exactly 40.0. All thresholds are inclusive.

`UNAVAILABLE` covers a failed forecast call. `PARTIAL` covers a response where
some fields are present and some are missing, which real APIs do.

### Scenarios

`SCENARIOS` pairs a place set with a context, a duration, and an expected
outcome in plain language.

```python
from tests.fixtures import get_scenario

s = get_scenario("dense_clear")
s["places"], s["context"], s["duration_min"], s["expect"]
```

Nineteen scenarios, including the duration tie cases — 30 must select bucket
20, and 50 must select bucket 40. The tie-break selects the **lower** bucket.

### Note on the data

Coordinates are real Melbourne locations so distances are plausible, but
`place_id` values are synthetic. Once `vicmap_app_ready.csv` is loadable, swap
in a handful of genuine records to confirm the shapes match.

## Running

```bash
cd server
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Check the fixtures load:

```bash
python -c "from tests.fixtures import SCENARIOS; print(len(SCENARIOS), 'scenarios')"
```

## Open questions

Tracked here until resolved, then removed.


- **Category string match** — confirm the seven values in the CSV match the
  `ActivityCategory` enum exactly, including case and underscores.
- **`display_name` null rate** — what proportion of real records are unnamed?
- **Category counts per LGA** — determines whether the zero-result path is a
  common case or an edge case.
- **Base combo templates** — story 3.1 makes "a base combo exists for the
  matched bucket" an eligibility condition. Seven categories across three
  buckets is 21 combinations minimum, and this work is currently unassigned.
