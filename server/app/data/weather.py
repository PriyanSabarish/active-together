import logging
from typing import Optional

import httpx
from aiolimiter import AsyncLimiter
from async_lru import alru_cache
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from app.config import settings
from app.models import Context

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    pass


# WeatherAPI's free tier  
_weatherapi_limiter = AsyncLimiter(max_rate=100, time_period=60)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _safe_get(client: httpx.AsyncClient, params: dict) -> Optional[httpx.Response]:
    async with _weatherapi_limiter:
        try:
            resp = await client.get(settings.weatherapi_url, params=params)
            if resp.status_code == 429:
                logger.warning("429 from WeatherAPI, retry-after=%s", resp.headers.get("Retry-After"))
                raise RateLimitError
            return resp
        except httpx.RequestError as exc:
            # network blip, not worth retrying here — let the caller treat it as unavailable
            logger.debug("request to WeatherAPI failed: %s", exc)
            return None


async def _execute_weather_fetch(lat: float, lon: float) -> Context:
    params = {
        "key": settings.weatherapi_key,
        "q": f"{lat},{lon}",
        "days": 1,       # need forecastday for daily_chance_of_rain
        "aqi": "yes",    # bundles air quality into the same call
    }

    async with httpx.AsyncClient(timeout=settings.open_meteo_timeout_seconds) as client:
        try:
            resp = await _safe_get(client, params)

            if not isinstance(resp, httpx.Response) or resp.status_code != 200:
                logger.warning("weather fetch failed: %s", getattr(resp, "status_code", "timeout"))
                return Context(available=False)

            data = resp.json()
            current = data.get("current", {})
            air_quality = current.get("air_quality", {})

            # WeatherAPI's current.json has no "chance of rain right now" — closest
            # equivalent is the day's forecasted chance of rain, 0-100 -> 0.0-1.0
            forecastday = data.get("forecast", {}).get("forecastday", [])
            daily_chance_of_rain = (
                forecastday[0].get("day", {}).get("daily_chance_of_rain")
                if forecastday else None
            )

            return Context(
                available=True,
                temp_c=current.get("temp_c"),
                precip_prob=(
                    daily_chance_of_rain / 100 if daily_chance_of_rain is not None else None
                ),
                wind_gust_kmh=current.get("gust_kph"),
                uv_index=current.get("uv"),
                pm25=air_quality.get("pm2_5"),
                pm10=air_quality.get("pm10"),
            )
        except Exception as exc:
            logger.error("weather context processing failed: %s", exc)
            return Context(available=False)


# rounding groups nearby coords onto the same cache key (~1.1km at 2dp)
# needs --workers 1 on Render or each process gets its own cache and this does nothing
@alru_cache(ttl=1800, maxsize=1000)
async def fetch_weather_context(lat: float, lon: float) -> Context:
    return await _execute_weather_fetch(round(lat, 2), round(lon, 2))