# Backend A — platform and data services

Owns getting data in and out: the database, spatial queries, external services,
the API surface and deployment.

Does **not** own scoring, tiering, ordering or explanation construction — those
belong to Backend B (`app/recommendation/`).

## Responsibilities

| Area | Detail |
|---|---|
| Database | Schema, loading `vicmap_app_ready.csv`, spatial indexing |
| Spatial queries | Radius search, distance calculation, boundary containment |
| External services | Open-Meteo forecast and air quality, caching, failure handling |
| API surface | `POST /recommendations`, request validation, error responses |
| Deployment | Hosting the API, seeding the deployed database |

## What Backend A provides

Three functions, consumed by Backend B and by the endpoint layer.

```python
get_candidates(lat, lng, radius_km) -> list[Place]
get_context(lat, lng, timestamp)    -> Context
is_within_pilot(lat, lng)           -> bool
```

### `get_candidates`

Returns candidate places within the radius, as `Place` objects.

- `distance_m` is calculated here via `ST_Distance` — Backend B does not compute
  distance from coordinates
- Uses `ST_DWithin` for the radius filter and `ST_Distance` for ordering
- `display_name` may be `None`; a share of FOI records have no usable name

```python
from app.models import Place, ActivityCategory

def get_candidates(lat, lng, radius_km) -> list[Place]:
    rows = db.execute(...)
    return [
        Place(
            place_id=r.place_id,
            display_name=r.display_name,
            activity_category=ActivityCategory(r.activity_category),
            lga_name=r.lga_name,
            latitude=r.latitude,
            longitude=r.longitude,
            distance_m=int(r.distance_m),
            classification_confidence=r.classification_confidence,
        )
        for r in rows
    ]
```

### `get_context`

Returns environmental data for a location and time.

**Returns a value on failure, does not raise.** This is the single most
important behaviour in this module — story 2.2 requires candidates to still be
shown with the weather labelled unavailable.

```python
from app.models import Context

def get_context(lat, lng, timestamp) -> Context:
    try:
        data = fetch_open_meteo(lat, lng, timestamp)
        return Context(available=True, temp_c=..., precip_prob=..., ...)
    except (TimeoutError, HTTPError):
        return Context(available=False)
```

Build the failure path at the same time as the success path. Retrofitting it
later changes the shape of every downstream call.

### `is_within_pilot`

Boundary containment against the versioned LGA geojson. Called before querying,
so an out-of-boundary request never reaches the database.

## Tasks

### Foundation

| ID | Task | Depends on | Unblocks |
|---|---|---|---|
| A1 | FastAPI scaffold, config, environment variables | Repository | A2, A3 |
| A2 | Places schema; load `vicmap_app_ready.csv` | Database provisioned | A4, A5 |
| A3 | Spatial index on place geometry | A2 | A4 performance |
| A4 | `get_candidates` — `ST_DWithin` + `ST_Distance` | A2, A3 | B integration; stories 1.1, 1.2 |
| A5 | `is_within_pilot` — boundary containment | A2, boundary resolved | Story 1.1 out-of-boundary path |

### External services

| ID | Task | Depends on | Unblocks |
|---|---|---|---|
| A6 | Open-Meteo forecast client — temperature, precipitation, wind gusts | A1 | Story 2.2 |
| A7 | Open-Meteo air-quality client — UV, PM2.5, PM10 | A1 | Story 2.3 |
| A8 | Expose forecast timestamps so the client can bound its time selector | A6 | Story 2.1 |
| A9 | Response caching by location bucket and hour | A6, A7 | Rate-limit protection |
| A10 | Graceful degradation — return `Context(available=False)` | A6, A7 | Story 2.2 unavailable path |

### API surface

| ID | Task | Depends on | Unblocks |
|---|---|---|---|
| A11 | `POST /recommendations` | A4, A6, A7, contract agreed | Client integration |
| A12 | Wire `get_candidates` and `get_context` into `recommend()` | A4, A6, A7, B6 | End-to-end flow |
| A13 | Coordinate precision guard — reject beyond 4dp | A11 | Privacy criterion |
| A14 | Dataset-unavailable response | A2, A11 | Story 3.1 error state |
| A15 | Request validation — radius 3/5/10, duration 20–120 | A11 | Stories 1.1, 2.1 |

### Deployment

| ID | Task | Depends on |
|---|---|---|
| A16 | Deploy the API where the client can reach it | A11 |
| A17 | Seed the deployed database | A2, A16 |
| A18 | Verify no secrets or connection strings are committed | A1 |

## Suggested order

```
A1 → A2 → A3 → A4 → A5 → A6 → A7 → A10 → A8 → A9
   → A11 → A15 → A13 → A12 → A14 → A16 → A17 → A18
```

A10 sits early on purpose — immediately after the two service clients.

## Three response shapes, three meanings

The client renders these differently. They must be distinguishable.

| Case | Owner | Response |
|---|---|---|
| No eligible candidates | B (B10) | `status: zero_results` with a message |
| Places dataset unreachable | A (A14) | HTTP error, not a zero-result |
| Forecast call failed | A (A10) | Normal response, `available: false` |

A dataset failure is not "no results found" — story 3.1 requires them to render
as different states.

## Needs from others

| Needs | From | Blocks |
|---|---|---|
| `vicmap_app_ready.csv` loadable | Data | A2 and everything after |
| Pilot boundary question resolved | Whole team | A5 |
| Database provisioned and reachable | Whoever owns provisioning | A2 |
| Client API contract agreed | Client | A11 |
| Confidence threshold placement decided | Data + Backend B | A4 |

## Open questions

- **Pilot boundary** — the data guide says Melbourne, Melton and Monash;
  acceptance criterion 1.1 says Melbourne and Monash. These do not match.
- **Confidence threshold** — filtered in the query here, in Backend B's
  eligibility check, or already applied by the pipeline?
- **Category strings** — do the seven values in the CSV match the
  `ActivityCategory` enum exactly, including case and underscores?
