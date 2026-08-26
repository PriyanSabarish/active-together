# Hourly Environment Context Data Guide

## 1. Purpose of the file

`hourly_environment_context.csv` is the integrated environmental context dataset
for the Active Together project. It combines cleaned Open-Meteo Weather Forecast
and Open-Meteo Air Quality data to support:

- weather lookup for a date and time selected by a parent;
- consideration of temperature, apparent temperature, precipitation, and wind
  when recommending outdoor activities;
- UV, PM2.5, and PM10 information when an air-quality forecast is available;
- environmental explanations for why an option was recommended or down-ranked;
- future context-matching and activity-place ranking logic.

This is a compact, product-facing dataset. It does not contain every metadata
field returned by the APIs. Raw JSON is stored under `data/raw/open_meteo/`, and
the separate cleaned datasets are stored under `data/processed/open_meteo/`.

## 2. Row grain

One row represents:

```text
The environmental conditions at one representative Metropolitan Melbourne LGA
point during one forecast hour
```

The current file covers 31 Metropolitan Melbourne municipalities. Each LGA has
168 weather forecast hours, giving 5,208 rows in total.

The composite primary key is:

```text
site_name + timestamp_utc
```

This combination must be unique. Do not identify duplicates using only
`site_name` or coordinates because each location appears once for every forecast
hour.

## 3. Why values change when coordinates stay the same

Coordinates describe a spatial location, while timestamps describe forecast
time. For an LGA such as Monash, every row uses the same representative
coordinate, but `timestamp_local` and `timestamp_utc` change from row to row.
Temperature, PM2.5, UV, precipitation probability, and wind may therefore change
every hour.

The following pattern is expected:

```text
site_name  latitude  longitude  timestamp_local          pm2_5_ugm3
monash     same      same       2026-08-26T00:00+10:00   3.8
monash     same      same       2026-08-26T01:00+10:00   3.9
monash     same      same       2026-08-26T02:00+10:00   4.4
```

It would be an integration error only if two rows had the same `site_name` and
`timestamp_utc` but conflicting environmental values. The integration script
checks for and rejects this condition.

## 4. Geographic coverage and spatial limitations

The location list is maintained in `pipeline/config/open_meteo_locations.csv`
and contains 31 Metropolitan Melbourne LGAs. The `latitude` and `longitude`
values are representative ABS ASGS 2025 LGA point coordinates. They are not:

- the user's live location;
- the coordinates of a specific park or activity place;
- the model grid-cell coordinates selected by Open-Meteo;
- monitoring-station coordinates that are equally representative of every part
  of an LGA.

The file is suitable for an LGA-level prototype and recommendation-logic
validation. It does not prove that environmental conditions are identical at
every location within an LGA. A single representative point is particularly
limited for large LGAs such as Cardinia, Yarra Ranges, and Mornington Peninsula.

For place-level accuracy, a future version should use Vicmap activity-place
coordinates and map nearby places to deduplicated Open-Meteo weather and
air-quality grid cells. It should not represent an entire LGA with one point.

## 5. Field definitions

| Field | Type/unit | Description |
|---|---|---|
| `site_name` | string | Machine-readable LGA identifier in lowercase snake_case, such as `greater_dandenong`. |
| `display_name` | string | Human-readable LGA name, such as `Greater Dandenong`. |
| `lga_code` | string | ABS 2025 LGA code. It should be read as a string. |
| `timestamp_local` | ISO 8601 | Forecast time in the Australia/Sydney timezone, including its UTC offset. |
| `timestamp_utc` | ISO 8601 | The same instant in UTC; recommended for joins and system storage. |
| `latitude` | decimal degrees | Latitude of the representative LGA request point in WGS84. |
| `longitude` | decimal degrees | Longitude of the representative LGA request point in WGS84. |
| `temperature_c` | °C | Forecast air temperature at 2 metres above ground. |
| `apparent_temperature_c` | °C | Perceived temperature combining factors such as humidity, wind, and radiation. |
| `precipitation_probability_pct` | % | Probability of precipitation for the hour, from 0 to 100. |
| `weather_code` | integer | WMO weather interpretation code. |
| `weather_description` | string | Machine-readable English description derived from `weather_code`. |
| `wind_speed_kmh` | km/h | Forecast wind speed at 10 metres above ground. |
| `wind_gusts_kmh` | km/h | Forecast wind gusts at 10 metres above ground. |
| `uv_index` | index | UV index from the Open-Meteo Air Quality API; blank when unavailable. |
| `pm2_5_ugm3` | µg/m³ | Forecast PM2.5 concentration; blank when unavailable. |
| `pm10_ugm3` | µg/m³ | Forecast PM10 concentration; blank when unavailable. |
| `air_quality_available` | boolean text | `true` when all three air-quality fields are available; otherwise `false`. |

Unit suffixes are included in field names to reduce ambiguity between the client
and server:

- `_c`: degrees Celsius;
- `_pct`: percentage;
- `_kmh`: kilometres per hour;
- `_ugm3`: micrograms per cubic metre.

## 6. Different Weather and Air Quality horizons

The Weather Forecast download currently covers seven days, or 168 hours per
LGA. The Air Quality download covers five days, but UV, PM2.5, and PM10 are all
missing in the final hour of the current API snapshot. The wrangling stage
removes these 31 completely empty rows, leaving 119 valid air-quality hours per
LGA.

The integration uses:

```text
Weather LEFT JOIN Air Quality
ON site_name + timestamp_utc
```

As a result:

- all 5,208 weather rows are retained;
- 3,689 rows also contain air-quality values;
- 1,519 rows contain weather only;
- rows without air-quality coverage keep UV, PM2.5, and PM10 blank and set
  `air_quality_available=false`;
- no mean imputation, forward filling, or interpolation is used to manufacture
  air-quality forecasts.

Applications must check `air_quality_available` before using UV or particulate
matter fields.

## 7. Recommended query method

Use the following key when retrieving conditions for an LGA and selected time:

```text
site_name + timestamp_utc
```

If the user selects a local time, convert it from `Australia/Sydney` to UTC
before matching. Do not join by CSV row number, coordinates alone, or an hour
number without a date.

Example:

```python
import pandas as pd

context = pd.read_csv(
    "data/processed/integrated/hourly_environment_context.csv",
    dtype={"lga_code": "string"},
    parse_dates=["timestamp_local", "timestamp_utc"],
)

selection = context.loc[
    (context["site_name"] == "monash")
    & (context["timestamp_utc"] == pd.Timestamp("2026-08-26T01:00:00Z"))
]
```

## 8. Usage cautions

- Values are forecasts, not observations or safety guarantees.
- Exploratory precipitation, UV, or particulate thresholds must not be treated
  automatically as medical or safety standards.
- `weather_description` is a code description, not a complete parent-facing
  advisory message.
- Adjacent LGAs may map to the same Open-Meteo model grid cell and therefore
  receive identical values.
- Large LGAs may contain meaningful internal spatial variation.
- Forecast ranges and values change whenever a new snapshot is downloaded.
- The server should provide explicit fallback behaviour for network failure,
  times outside the forecast horizon, and unavailable air-quality data.

## 9. Sources and generation workflow

Data sources:

- Open-Meteo Weather Forecast API;
- Open-Meteo Air Quality API;
- ABS ASGS 2025 LGA point coordinates.

Generation order:

```powershell
python pipeline/exploration/download_open_meteo.py
python pipeline/exploration/explore_open_meteo.py
python pipeline/wrangling/wrangle_weather_forecast.py
python pipeline/wrangling/wrangle_air_quality.py
python pipeline/integration/build_open_meteo_context.py
```

The final integration logic is implemented in:

```text
pipeline/integration/build_open_meteo_context.py
```

After updating the raw snapshots, rerun exploration, wrangling, and integration,
then review the validation reports before the server consumes the new output.
