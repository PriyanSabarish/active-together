# Open-Meteo exploration data

From the repository root, run:

```powershell
python pipeline/exploration/download_open_meteo.py
```

This creates three dated files under `data/raw/open_meteo/`:

- `weather_forecast_YYYY-MM-DD.json`
- `air_quality_YYYY-MM-DD.json`
- `download_manifest_YYYY-MM-DD.json`

The snapshot covers the 31 Metropolitan Melbourne municipalities using ABS 2025
LGA point coordinates from `pipeline/config/open_meteo_locations.csv`. Weather
contains seven days of hourly values; air quality contains its default reliable
five-day hourly window. Forecast fields cover temperature, apparent temperature,
precipitation probability, weather code, wind speed, and wind gusts. Air-quality
fields cover UV index, PM2.5, and PM10.

The snapshot JSON files in `data/raw/` are intentionally ignored by Git. Each group member can recreate the
same directory structure without merging dynamic API snapshots. The dated
manifest records the exact request URLs used for a snapshot.

Source: Open-Meteo Forecast API and Open-Meteo Air Quality API. Data is
available under CC BY 4.0. Attribution: Weather data by Open-Meteo.com.
