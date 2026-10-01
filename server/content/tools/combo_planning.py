"""Prepare development timetables from explicitly chosen activities and draft estimates."""

from pathlib import Path

from jsonschema import Draft202012Validator

from content.tools.activity_library import AGE_BANDS, CONTENT_DIR, load_preview_activities, read_yaml


def validate_profiles(profiles, activities):
    """Check exact activity versions, age coverage and available extension references."""
    by_id = {activity["activity_id"]: activity for activity in activities}
    indexed = {}
    for profile in profiles:
        activity_id = profile["activity_id"]
        if activity_id in indexed:
            raise ValueError("Duplicate duration profile: " + activity_id)
        if activity_id not in by_id:
            raise ValueError("Unknown activity in duration profiles: " + activity_id)
        activity = by_id[activity_id]
        if profile["activity_version"] != activity["version"]:
            raise ValueError("Duration estimate needs review after version change: " + activity_id)
        if set(profile["base_minutes"]) != set(activity["age_variants"]):
            raise ValueError("Duration age bands must match the activity: " + activity_id)
        if profile["max_extra_rounds"] and profile["extension_index"] >= len(activity["adaptations"]["extend"]):
            raise ValueError("Missing authored extension: " + activity_id)
        indexed[activity_id] = profile
    missing = sorted(set(by_id) - set(indexed))
    if missing:
        raise ValueError("Missing duration profiles: " + ", ".join(missing))
    return indexed


def load_duration_rules(activities, content_dir=CONTENT_DIR):
    """Load and validate the separate draft timing configuration."""
    content_dir = Path(content_dir)
    schema = read_yaml(content_dir / "schema/duration_profiles.schema.yaml")
    Draft202012Validator.check_schema(schema)
    config = read_yaml(content_dir / "planning/duration_profiles.yaml")
    error = next(Draft202012Validator(schema).iter_errors(config), None)
    if error:
        raise ValueError("Invalid duration configuration: " + error.message)
    profiles = validate_profiles(config["activity_profiles"], activities)
    for minutes, bucket in config["combo_buckets"].items():
        overhead = bucket["preparation_minutes"] + (bucket["activity_count"] - 1) * (
            bucket["rest_between_minutes"] + bucket["transition_between_minutes"])
        if overhead >= int(minutes):
            raise ValueError("Preparation and breaks leave no activity time: " + minutes)
    return config, profiles


def build_combo_preview(activity_ids, age_band, duration_bucket, content_dir=CONTENT_DIR):
    """Allocate bounded optional rounds; report spare time or an over-budget plan."""
    activities = load_preview_activities(content_dir)
    config, profiles = load_duration_rules(activities, content_dir)
    if age_band not in AGE_BANDS:
        raise ValueError("Unsupported age band.")
    if type(duration_bucket) is not int or str(duration_bucket) not in config["combo_buckets"]:
        raise ValueError("Duration must be 20, 40 or 60 minutes.")
    bucket = config["combo_buckets"][str(duration_bucket)]
    if len(activity_ids) != bucket["activity_count"] or len(set(activity_ids)) != len(activity_ids):
        raise ValueError(f"Choose {bucket['activity_count']} different activity IDs for this bucket.")
    by_id = {activity["activity_id"]: activity for activity in activities}
    blocks = [{"kind": "preparation", "minutes": bucket["preparation_minutes"]}]
    activity_blocks = []
    for index, activity_id in enumerate(activity_ids):
        if activity_id not in by_id or age_band not in by_id[activity_id]["age_variants"]:
            raise ValueError("Activity or requested age unavailable: " + activity_id)
        if index:
            blocks.append({"kind": "rest", "minutes": bucket["rest_between_minutes"]})
            blocks.append({"kind": "transition", "minutes": bucket["transition_between_minutes"]})
        profile = profiles[activity_id]
        block = {
            "kind": "activity", "activity_id": activity_id,
            "activity_version": by_id[activity_id]["version"], "age_band": age_band,
            "base_minutes": profile["base_minutes"][age_band],
            "minutes": profile["base_minutes"][age_band], "extra_rounds": 0,
            "extension": None,
        }
        blocks.append(block)
        activity_blocks.append(block)
    remaining = duration_bucket - sum(block["minutes"] for block in blocks)
    # Add at most the configured number of authored extensions, in the chosen order.
    for round_index in range(max(profiles[item]["max_extra_rounds"] for item in activity_ids)):
        for block in activity_blocks:
            profile = profiles[block["activity_id"]]
            if round_index < profile["max_extra_rounds"] and profile["extension_minutes"] <= remaining:
                block["minutes"] += profile["extension_minutes"]
                block["extra_rounds"] += 1
                block["extension"] = by_id[block["activity_id"]]["adaptations"]["extend"][profile["extension_index"]]
                remaining -= profile["extension_minutes"]
    status = "fits_estimate" if remaining == 0 else "unused_time"
    if remaining < 0:
        status = "over_budget"
    return {
        "schema_version": "0.1.0", "mode": "development_preview",
        "timing_basis": config["timing_basis"], "duration_bucket": duration_bucket,
        "age_band": age_band, "status": status, "blocks": blocks,
        "scheduled_minutes": sum(block["minutes"] for block in blocks),
        "unused_minutes": max(0, remaining), "over_budget_minutes": max(0, -remaining),
    }
