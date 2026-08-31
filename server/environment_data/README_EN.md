# Active Together Environment Data

This is a standalone Python module that can be imported directly by the backend. It provides weather and air-quality context for the three pilot LGAs:

- City of Melton (`24650`, `melton`)
- City of Melbourne (`24600`, `melbourne`)
- City of Monash (`24970`, `monash`)

The module uses only the Python standard library. Live API responses and downloaded seven-day forecasts are converted into the same `EnvironmentContext` model and evaluated by the same Concept V2 environmental rules.

## Structure

```text
server/environment_data/
├── config/pilot_locations.csv   Three pilot LGAs and representative coordinates
├── open_meteo_client.py         Open-Meteo requests and timeout handling
├── normalizer.py                Weather and AQ merging by UTC hour
├── models.py                    Shared backend data models
├── policy.py                    Concept V2 environmental thresholds
├── cache.py                     Gzip storage, checksums, atomic updates and lookup
├── service.py                   Live-first service with cache fallback
├── build_offline_bundle.py      Seven-day bundle CLI
├── backend_example.py           Framework-neutral backend example
└── tests/                       Standard-library unit tests
```

## Build the seven-day offline bundle

Run the following command from the repository root:

```powershell
python -m server.environment_data.build_offline_bundle
```

The default output is:

```text
data/environment_cache/environment-bundle-v1.json.gz
```

Both weather and air-quality requests explicitly use `forecast_days=7`. If the air-quality request fails independently, the module still creates a valid weather bundle. The AQ fields remain `null`, with `air_quality_available=false`; values are never interpolated or invented.

An update is written to a temporary file first. The module validates its structure and checksum before atomically replacing the existing bundle. A failed update therefore does not damage the last valid bundle.

The completed bundle must contain exactly:

```text
3 locations × 168 hourly records = 504 records
```

All three locations must have the same UTC hourly time axis.

## Backend integration

```python
from pathlib import Path

from server.environment_data.backend_example import create_environment_service


environment_service = create_environment_service(
    Path("data/environment_cache")
)

result = environment_service.get_context(
    site_name="monash",
    requested_at=user_selected_datetime,
)

return result.to_dict()
```

The backend can expose routes such as:

```text
GET  /api/v1/environment/context?site_name=monash&at=<ISO-8601>
POST /api/v1/environment/cache/refresh
GET  /api/v1/environment/cache/status
```

The `at` value must contain a timezone offset, for example:

```text
2026-09-02T17:00:00+10:00
```

The requested time is converted to UTC and rounded down to the start of the hour. The returned `timestamp_local` is converted to `Australia/Sydney` for display.

## Live and offline behaviour

The service follows this order:

1. Request the current seven-day forecast from Open-Meteo.
2. Validate and normalize the weather response.
3. Merge air-quality values by `site_name + timestamp_utc` when available.
4. Save a successful live forecast to `latest-live-forecast-v1.json.gz`.
5. Return the requested live hourly record.
6. If the live request or response fails, search the most recent live cache.
7. If it is not available there, search the downloaded offline bundle.
8. If neither cache contains the requested hour, raise `EnvironmentUnavailable`.

The service never extrapolates beyond the downloaded forecast range.

An air-quality failure does not invalidate usable weather data. In that situation, weather is returned normally, while AQ is explicitly marked unavailable.

## Response structure

```json
{
  "context": {
    "lga_code": "24970",
    "site_name": "monash",
    "display_name": "City of Monash",
    "latitude": -37.89673562404778,
    "longitude": 145.1412216752278,
    "source_mode": "cached",
    "timestamp_utc": "2026-09-02T07:00:00+00:00",
    "timestamp_local": "2026-09-02T17:00:00+10:00",
    "fetched_at_utc": "2026-08-31T03:00:00+00:00",
    "temperature_c": 16.2,
    "apparent_temperature_c": 15.8,
    "precipitation_probability_pct": 20,
    "weather_code": 2,
    "weather_description": "partly_cloudy",
    "wind_speed_kmh": 15,
    "wind_gusts_kmh": 28,
    "uv_index": 4.1,
    "pm2_5_ugm3": 8.4,
    "pm10_ugm3": 14.2,
    "weather_available": true,
    "air_quality_available": true
  },
  "assessment": {
    "tier": "normal",
    "show_uv_reminder": true,
    "warnings": [],
    "unavailable_fields": []
  }
}
```

The `source_mode` value is:

- `live` when the current API request succeeded;
- `cached` when the result came from either the latest-live cache or the downloaded offline bundle.

## Concept V2 environmental rules

- Precipitation probability `>= 60%`: place the outdoor candidate in the deprioritised environmental tier.
- Wind gusts `>= 40 km/h`: place the outdoor candidate in the deprioritised environmental tier.
- PM2.5 `>= 25 µg/m³`: place the outdoor candidate in the deprioritised environmental tier.
- PM10 `>= 80 µg/m³`: place the outdoor candidate in the deprioritised environmental tier.
- UV index `>= 3`: show a sun-protection reminder, but do not deprioritise a candidate based on UV alone.
- Missing values are marked unavailable. They are not estimated or interpolated.

The recommendation layer should use `assessment.tier` for ordering:

1. normal-tier candidates;
2. deprioritised candidates;
3. approximate distance and then place name within each tier.

The environmental tier is contextual information, not a safety or medical conclusion. A deprioritised result should not automatically be removed when no normal-tier candidate is available.

## Pilot-location validation

The accepted `site_name` values are exactly:

```text
melton
melbourne
monash
```

An unsupported value raises `UnknownPilotLocation`.

The backend must use council-boundary data to determine which pilot LGA contains the user's selected point before calling this module. It must not assign an LGA by selecting whichever of the three representative coordinates is closest.

## Spatial-resolution limitation

The current MVP uses one representative coordinate per LGA, so the returned conditions are regional forecasts rather than measurements at the user's exact position.

This limitation is particularly important for the City of Melton because of its larger geographic area. If greater spatial precision is required later, the preferred approach is to add multiple forecast sample points within Melton and choose the nearest valid sample point after the user's LGA has been determined.

Downloading a separate forecast for every FOI place is not recommended because many places resolve to the same underlying forecast-model grid cell.

## Cache status

The backend can inspect cache availability without making a network request:

```python
status = environment_service.repository.status()
```

The result reports, for both live and offline caches:

- availability;
- number of records;
- included sites;
- forecast start and end times;
- forecast retrieval time;
- validation errors, when applicable.

## Error handling

The main service exceptions are:

- `UnknownPilotLocation`: the requested `site_name` is not one of the three pilot LGAs;
- `EnvironmentUnavailable`: neither the live API nor a validated cache contains the requested hour;
- `OpenMeteoError`: the provider request failed or returned an unexpected top-level response;
- `NormalizationError`: required hourly arrays are missing, inconsistent or invalid;
- `CacheError`: a cache is malformed, incomplete or fails checksum validation.

The HTTP layer can map these to appropriate responses. For example:

```text
UnknownPilotLocation    -> 400 Bad Request
EnvironmentUnavailable -> 503 Service Unavailable
```

Do not expose internal provider errors or filesystem paths directly to the client.

## Tests

Run the tests from the repository root:

```powershell
python -m unittest discover -s server/environment_data/tests -v
```

The tests do not access the network. They cover:

- the exact three-LGA scope;
- threshold boundary values;
- UV reminders without automatic deprioritisation;
- weather operation when AQ is unavailable;
- weather and AQ merging by UTC hour;
- cache serialization and checksum validation;
- live-request failure and offline fallback;
- rejection of requests outside the cached forecast range.

## Important product-language constraint

When `source_mode="cached"`, the interface should say that it is using a forecast downloaded at `fetched_at_utc`. It must not label cached data as current or live weather.

Environmental wording must remain informational and leave the final activity decision to the parent. It must not claim that a location or activity is safe, and it must not provide medical advice.
