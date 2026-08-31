"""Concept V2 environmental rules shared by live and offline modes."""

from __future__ import annotations

from .models import EnvironmentAssessment, EnvironmentContext


RAIN_THRESHOLD_PCT = 60.0
WIND_GUST_THRESHOLD_KMH = 40.0
PM25_THRESHOLD_UGM3 = 25.0
PM10_THRESHOLD_UGM3 = 80.0
UV_REMINDER_THRESHOLD = 3.0


def assess_environment(context: EnvironmentContext) -> EnvironmentAssessment:
    warnings: list[str] = []
    unavailable: list[str] = []
    deprioritised = False

    if not context.weather_available:
        unavailable.append("weather")
    else:
        if context.precipitation_probability_pct is None:
            unavailable.append("precipitation_probability")
        elif context.precipitation_probability_pct >= RAIN_THRESHOLD_PCT:
            deprioritised = True
            warnings.append("high_precipitation_probability")

        if context.wind_gusts_kmh is None:
            unavailable.append("wind_gusts")
        elif context.wind_gusts_kmh >= WIND_GUST_THRESHOLD_KMH:
            deprioritised = True
            warnings.append("strong_wind_gusts")

    if not context.air_quality_available:
        unavailable.append("air_quality")
    else:
        if context.pm2_5_ugm3 is None:
            unavailable.append("pm2_5")
        elif context.pm2_5_ugm3 >= PM25_THRESHOLD_UGM3:
            deprioritised = True
            warnings.append("elevated_pm2_5")

        if context.pm10_ugm3 is None:
            unavailable.append("pm10")
        elif context.pm10_ugm3 >= PM10_THRESHOLD_UGM3:
            deprioritised = True
            warnings.append("elevated_pm10")

        if context.uv_index is None:
            unavailable.append("uv_index")

    show_uv_reminder = (
        context.uv_index is not None and context.uv_index >= UV_REMINDER_THRESHOLD
    )
    return EnvironmentAssessment(
        tier="deprioritised" if deprioritised else "normal",
        show_uv_reminder=show_uv_reminder,
        warnings=tuple(warnings),
        unavailable_fields=tuple(unavailable),
    )
