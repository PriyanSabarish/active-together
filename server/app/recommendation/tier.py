from __future__ import annotations

from app.models import Context, EnvironmentalSummary, Tier
from app.recommendation.thresholds import DEPRIORITISE, THRESHOLDS, Threshold


def assess(
    context: Context,
    thresholds: tuple[Threshold, ...] = THRESHOLDS,
) -> tuple[Tier, EnvironmentalSummary]:
    """Evaluate environmental context against active thresholds to determine tier and alerts."""
    warnings: list[str] = []
    reminders: list[str] = []

    if context.available:
        for threshold in thresholds:
            reading = getattr(context, threshold.field)
            if not threshold.triggers(reading):
                continue

            if threshold.effect == DEPRIORITISE:
                warnings.append(threshold.message)
            else:
                reminders.append(threshold.message)

    tier = Tier.DEPRIORITISED if warnings else Tier.NORMAL

    summary = EnvironmentalSummary(
        available=context.available,
        temp_c=context.temp_c,
        precip_prob=context.precip_prob,
        wind_gust_kmh=context.wind_gust_kmh,
        uv_index=context.uv_index,
        pm25=context.pm25,
        pm10=context.pm10,
        warnings=tuple(warnings),
        reminders=tuple(reminders),
    )

    return tier, summary