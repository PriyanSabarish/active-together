import logging
import httpx

from app.config import settings
from app.models import Context

logger = logging.getLogger(__name__)


async def fetch_weather_context(lat: float, lon: float) -> Context:
    fc_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,precipitation_probability,wind_gusts_10m,uv_index",
    }
    aq_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "pm2_5,pm10",
    }

    async with httpx.AsyncClient(timeout=settings.open_meteo_timeout_seconds) as client:
        try:
            fc_resp = await client.get(settings.open_meteo_forecast_url, params=fc_params)
            if fc_resp.status_code != 200:
                logger.warning("Forecast request failed with status %s", fc_resp.status_code)
                return Context(available=False)

            fc_data = fc_resp.json().get("current", {})

            # Open-Meteo returns precipitation_probability as 0-100; the
            # Context contract (and every threshold/explanation that reads
            # precip_prob) expects a 0.0-1.0 fraction.
            precip_prob_pct = fc_data.get("precipitation_probability")
            precip_prob = precip_prob_pct / 100 if precip_prob_pct is not None else None

            # Air quality is optional; if it fails, context stays valid with None fields
            pm25, pm10 = None, None
            try:
                aq_resp = await client.get(settings.open_meteo_air_quality_url, params=aq_params)
                if aq_resp.status_code == 200:
                    aq_data = aq_resp.json().get("current", {})
                    pm25 = aq_data.get("pm2_5")
                    pm10 = aq_data.get("pm10")
            except httpx.RequestError as exc:
                logger.debug("Air quality endpoint unavailable: %s", exc)

            return Context(
                available=True,
                temp_c=fc_data.get("temperature_2m"),
                precip_prob=precip_prob,
                wind_gust_kmh=fc_data.get("wind_gusts_10m"),
                uv_index=fc_data.get("uv_index"),
                pm25=pm25,
                pm10=pm10,
            )

        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.error("Failed to fetch weather context: %s", exc)
            return Context(available=False)