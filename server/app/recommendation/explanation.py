"""
Explanation construction (task B8), story 3.3.

The explanation is assembled from clauses. A clause is emitted only when the
value behind it is present, so a missing value produces a shorter sentence
rather than a guess.

Deliberately absent: adjectives. The frontend mock reads "mild and dry at
4pm", but "mild" is an interpretation of 19 degrees that no source verified,
and "dry" is an interpretation of a probability. The clause states the values
and lets the parent judge, per story 2.2's requirement that wording is
informational and leaves the decision to them.

Thetext is not written here — it comes from the threshold config (B3),
so all parent-facing environmental wording stays reviewable in one file.
"""

from __future__ import annotations

from datetime import datetime

from app.models import EnvironmentalSummary

WEATHER_UNAVAILABLE = "Weather data is unavailable for this time."


def distance_clause(distance_m: int) -> str:
    """Approximate straight-line distance, per story 1.2's wording."""
    if distance_m >= 1000:
        return f"About {distance_m / 1000:.1f} km away."
    # Round to the nearest 10 m. The underlying figure is straight-line and
    # approximate; more precision than that would overstate it.
    return f"About {round(distance_m, -1)} m away."


def duration_clause(entered_duration_min: int, bucket: int) -> str:
    """Both the entered value and the matched bucket, per story 2.1."""
    return (
        f"Fits your {entered_duration_min} minute window "
        f"using the {bucket} minute plan."
    )


def time_clause(timestamp: str | None) -> str | None:
    """The selected forecast time. Omitted when no timestamp was supplied.

    The seam signature does not carry a timestamp, so this is frequently
    None. Omitting is correct: story 3.3 forbids estimating a value that is
    not available.
    """
    if not timestamp:
        return None
    try:
        when = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    # Formatted by hand rather than with strftime: the no-padding flag is
    # %-I on Linux and %#I on Windows, and the team runs both.
    hour = when.hour % 12 or 12
    meridiem = "am" if when.hour < 12 else "pm"
    if when.minute:
        return f"Forecast for {hour}:{when.minute:02d}{meridiem}."
    return f"Forecast for {hour}{meridiem}."


def weather_clause(summary: EnvironmentalSummary) -> str:
    """Available environmental readings, or an explicit unavailable label."""
    if not summary.available:
        return WEATHER_UNAVAILABLE

    parts: list[str] = []
    if summary.temp_c is not None:
        parts.append(f"{round(summary.temp_c)} degrees")
    if summary.precip_prob is not None:
        percent = round(summary.precip_prob * 100)
        # "an 85% chance", not "a 85% chance". Covers 8, 11, 18 and the 80s,
        # which is every case a 0-100 percentage can produce.
        article = "an" if str(percent).startswith(("8", "11", "18")) else "a"
        parts.append(f"{article} {percent}% chance of rain")

    if not parts:
        return WEATHER_UNAVAILABLE
    if len(parts) == 1:
        return f"{parts[0].capitalize()} at this time."
    return f"{parts[0].capitalize()} with {parts[1]}."


def build_explanation(
    distance_m: int,
    entered_duration_min: int,
    bucket: int,
    summary: EnvironmentalSummary,
    timestamp: str | None = None,
) -> str:
    """Assemble the explanation from clauses, skipping any that have no value."""
    warnings = summary.warnings if summary.warnings is not None else ()
    reminders = summary.reminders if summary.reminders is not None else ()

    clauses: list[str | None] = [
        distance_clause(distance_m),
        time_clause(timestamp),
        duration_clause(entered_duration_min, bucket),
        weather_clause(summary),
        *warnings,
        *reminders,
    ]
    return " ".join(c for c in clauses if c)