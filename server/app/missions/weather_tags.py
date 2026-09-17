"""
Classifies environmental Context into the WeatherTag values a template's
weather_tags list can be matched against — the weather dimension of
select_templates (B20).

WET and WINDY reuse the deprioritisation thresholds already agreed for
iteration 1 (app/recommendation/thresholds.json), rather than inventing a
second set of numbers for the same conditions. HOT and COLD have no prior
threshold in this codebase; the cutoffs below are new, reasonable Melbourne
defaults and easy to retune later. OVERCAST is never produced — Context
carries no cloud-cover field — so a template tagged only "overcast" is
only reachable via ANY today.

Missing readings never trigger a condition (the same convention as
app.recommendation.thresholds.Threshold.triggers), so DRY is the default
whenever precipitation data is unavailable rather than blocking selection
on missing weather.
"""

from __future__ import annotations

from app.missions.models import WeatherTag
from app.models import Context

WET_PRECIP_PROB = 0.60  # matches app/recommendation/thresholds.json precip_prob
WINDY_GUST_KMH = 40.0  # matches app/recommendation/thresholds.json wind_gust_kmh
HOT_TEMP_C = 30.0
COLD_TEMP_C = 12.0


def classify_weather_tags(context: Context) -> frozenset[WeatherTag]:
    tags = {WeatherTag.ANY}

    is_wet = context.precip_prob is not None and context.precip_prob >= WET_PRECIP_PROB
    tags.add(WeatherTag.WET if is_wet else WeatherTag.DRY)

    if context.wind_gust_kmh is not None and context.wind_gust_kmh >= WINDY_GUST_KMH:
        tags.add(WeatherTag.WINDY)

    if context.temp_c is not None:
        if context.temp_c >= HOT_TEMP_C:
            tags.add(WeatherTag.HOT)
        elif context.temp_c <= COLD_TEMP_C:
            tags.add(WeatherTag.COLD)

    return frozenset(tags)
