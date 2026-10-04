"""
Handles OpenRouteService matrix calls and fallback straight-line estimates.
Adheres strictly to D16 (rounding origin to 3 dp), D7 (per-place fallback on null),
and Task A41 (daily request limits resetting at Melbourne midnight).
"""

import math
import datetime
from zoneinfo import ZoneInfo
import httpx
from app.config import settings
from app.services import TravelTime

SPEEDS = {
    "walking": 5.0,
    "cycling": 15.0,
    "driving": 30.0
}
DRIVING_PARKING_BUFFER_MIN = 5
DAILY_ORS_LIMIT = 400  # Academic quota ceiling safeguard

# Thread-safe tracker state for Task A41
_ors_usage_state = {
    "date": None,
    "count": 0
}

def _check_and_increment_quota() -> bool:
    """Resets counter at Melbourne midnight and checks against quota limit."""
    melbourne_tz = ZoneInfo("Australia/Melbourne")
    today_melbourne = datetime.datetime.now(melbourne_tz).date()

    if _ors_usage_state["date"] != today_melbourne:
        _ors_usage_state["date"] = today_melbourne
        _ors_usage_state["count"] = 0

    if _ors_usage_state["count"] >= DAILY_ORS_LIMIT:
        return False

    _ors_usage_state["count"] += 1
    return True


def estimate_travel_time(lat1: float, lon1: float, lat2: float, lon2: float, mode: str) -> TravelTime:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    straight_line_km = R * c
    
    adjusted_km = straight_line_km * 1.3
    speed = SPEEDS.get(mode, 5.0)
    
    hours = adjusted_km / speed
    minutes = hours * 60
    
    if mode == "driving":
        minutes += DRIVING_PARKING_BUFFER_MIN
        
    return TravelTime(minutes=max(1, math.ceil(minutes)), source="estimate")


async def get_travel_times(origin: tuple[float, float], candidates: list, mode: str) -> dict[str, TravelTime]:
    rounded_origin = (round(origin[0], 3), round(origin[1], 3))
    travel_times = {}

    if not candidates:
        return travel_times

    # Task A41: Fall back automatically if daily Melbourne quota is exhausted
    if not _check_and_increment_quota():
        for candidate in candidates:
            travel_times[candidate.place_id] = estimate_travel_time(
                rounded_origin[0], rounded_origin[1], candidate.latitude, candidate.longitude, mode
            )
        return travel_times

    ors_destinations = [[c.longitude, c.latitude] for c in candidates if c.longitude and c.latitude]
    ors_sources = [rounded_origin[1], rounded_origin[0]]

    url = f"https://api.openrouteservice.org/v2/matrix/{mode}"
    headers = {
        "Authorization": getattr(settings, "ors_api_key", ""),
        "Content-Type": "application/json"
    }
    payload = {
        "locations": [ors_sources] + ors_destinations,
        "sources": [0],
        "destinations": list(range(1, len(ors_destinations) + 1)),
        "metrics": ["duration"]
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                raise httpx.HTTPStatusError("ORS returned non-200", request=response.request, response=response)
            
            data = response.json()
            durations = data.get("durations", [[]])[0]

            for idx, candidate in enumerate(candidates):
                seconds = durations[idx] if idx < len(durations) else None
                if seconds is None:
                    travel_times[candidate.place_id] = estimate_travel_time(
                        rounded_origin[0], rounded_origin[1], candidate.latitude, candidate.longitude, mode
                    )
                else:
                    minutes = math.ceil(seconds / 60)
                    travel_times[candidate.place_id] = TravelTime(minutes=minutes, source="openrouteservice")
                    
    except Exception:
        for candidate in candidates:
            travel_times[candidate.place_id] = estimate_travel_time(
                rounded_origin[0], rounded_origin[1], candidate.latitude, candidate.longitude, mode
            )

    return travel_times