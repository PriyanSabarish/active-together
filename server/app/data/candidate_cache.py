"""Result cache and "dataset unavailable" state for place lookups (A57-A60).

Candidate places are cached by rounded origin (3 dp, the same rounding the
travel-time call uses), radius and setting, and keyed to DATASET_VERSION so
bumping that after a pipeline refresh invalidates every entry at once.

Only a successful load is stored. A miss whose load fails raises
DatasetUnavailable: the caller turns that into the "places are temporarily
unavailable" state, never an empty list that reads as "nothing nearby".

The cache is per worker process. That is safe because it only holds read-only
query results.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from app.config import settings

logger = logging.getLogger("uvicorn.error")

_cache: dict[tuple, tuple[float, list]] = {}
MAX_ENTRIES = 500


class DatasetUnavailable(Exception):
    """The places dataset could not be read and nothing cached covers the request."""


def clear() -> None:
    _cache.clear()


def get_candidates(db, lat: float, lon: float, radius_km: float, setting: str, loader: Callable) -> list:
    rlat, rlon = round(lat, 3), round(lon, 3)
    key = (rlat, rlon, radius_km, setting, settings.dataset_version)
    now = time.monotonic()

    hit = _cache.get(key)
    if hit and hit[0] > now:
        return hit[1]

    try:
        value = loader(db, lat=rlat, lon=rlon, radius_km=radius_km)
    except Exception as exc:
        logger.error("Place lookup failed (%s): %s", setting, type(exc).__name__)
        raise DatasetUnavailable() from exc

    if len(_cache) >= MAX_ENTRIES:
        _cache.pop(next(iter(_cache)))
    _cache[key] = (now + settings.candidate_cache_ttl_s, value)
    return value
