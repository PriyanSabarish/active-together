import asyncio
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


_meteo_limiter = AsyncLimiter(max_rate=60, time_period=60)  # cap outbound calls, shared IP gets throttled fast


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _safe_get(client: httpx.AsyncClient, url: str, params: dict) -> Optional[httpx.Response]:
    async with _meteo_limiter:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                logger.warning("429 from %s, retry-after=%s", url, resp.headers.get("Retry-After"))
                raise RateLimitError
            return resp
        except httpx.RequestError as exc:
            # network blip, not worth retrying here — let the caller treat it as unavailable
            logger.debug("request to %s failed: %s", url, exc)
            return None


async def _execute_weather_fetch(lat: float, lon: float) -> Context:
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
        # forecast + air quality in parallel, one round trip's worth of latency
        fc_task = _safe_get(client, settings.open_meteo_forecast_url, fc_params)
        aq_task = _safe_get(client, settings.open_meteo_air_quality_url, aq_params)

        try:
            fc_resp, aq_resp = await asyncio.gather(fc_task, aq_task, return_exceptions=True)

            # forecast is required — no forecast, no context
            if not isinstance(fc_resp, httpx.Response) or fc_resp.status_code != 200:
                logger.warning("forecast fetch failed: %s", getattr(fc_resp, "status_code", "timeout"))
                return Context(available=False)

            fc_data = fc_resp.json().get("current", {})
            precip_pct = fc_data.get("precipitation_probability")

            # air quality is a nice-to-have, don't fail the whole context over it
            pm25, pm10 = None, None
            if isinstance(aq_resp, httpx.Response) and aq_resp.status_code == 200:
                aq_data = aq_resp.json().get("current", {})
                pm25 = aq_data.get("pm2_5")
                pm10 = aq_data.get("pm10")

            return Context(
                available=True,
                temp_c=fc_data.get("temperature_2m"),
                precip_prob=precip_pct / 100 if precip_pct is not None else None,  # API gives 0-100, we want 0-1
                wind_gust_kmh=fc_data.get("wind_gusts_10m"),
                uv_index=fc_data.get("uv_index"),
                pm25=pm25,
                pm10=pm10,
            )
        except Exception as exc:
            logger.error("weather context processing failed: %s", exc)
            return Context(available=False)


# rounding groups nearby coords onto the same cache key (~1.1km at 2dp)
# needs --workers 1 on Render or each process gets its own cache and this does nothing
@alru_cache(ttl=1800, maxsize=1000)
async def fetch_weather_context(lat: float, lon: float) -> Context:
    return await _execute_weather_fetch(round(lat, 2), round(lon, 2))