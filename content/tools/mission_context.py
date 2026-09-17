"""Validate content bindings and demonstrate conservative contextual matching."""

from pathlib import Path

from jsonschema import Draft202012Validator

from content.tools.activity_library import CONTENT_DIR, read_yaml


def load_context_bindings(families, content_dir=CONTENT_DIR):
    """Check content tags without inventing client preference IDs or site capabilities."""
    content_dir = Path(content_dir)
    config = read_yaml(content_dir / "taxonomy/mission_context_bindings.yaml")
    schema = read_yaml(content_dir / "schema/mission_context.validation.yaml")
    Draft202012Validator.check_schema(schema)
    error = next(Draft202012Validator(schema).iter_errors(config), None)
    if error:
        raise ValueError("Invalid context bindings: " + error.message)
    taxonomy = read_yaml(content_dir / "taxonomy/activity_types.yaml")
    types = {item["id"] for item in taxonomy["activity_types"]}
    indexed = {}
    for binding in config["templates"]:
        template_id = binding["template_id"]
        if template_id in indexed or template_id != "activity_" + binding["source_activity_id"]:
            raise ValueError("Duplicate or mismatched binding: " + template_id)
        if binding["activity_type"] not in types:
            raise ValueError("Unknown activity type in binding: " + template_id)
        if config["preference_binding_status"] == "unbound" and binding["preference_codes"]:
            raise ValueError("Unbound preferences cannot claim real client codes")
        if config["preference_binding_status"] == "bound" and not binding["preference_codes"]:
            raise ValueError("Bound preferences need actual client codes for every family")
        indexed[template_id] = binding
    if any(family["template_id"] not in indexed for family in families):
        raise ValueError("Every selected family needs context bindings")
    return config, indexed


def assess_conditions(template, binding, place, context, preferences=None, preference_binding_status="unbound"):
    """Return a draft candidate decision; the caller supplies verified context, not raw AQI."""
    if not isinstance(place, dict) or not isinstance(context, dict):
        raise ValueError("Place and context must be normalized objects")
    if preference_binding_status not in ("unbound", "bound"):
        raise ValueError("Unknown preference binding status")
    if preferences is not None:
        if not isinstance(preferences, dict) or set(preferences) - {"excluded_codes", "preferred_codes"}:
            raise ValueError("Preferences must use normalized excluded_codes and preferred_codes")
        for codes in preferences.values():
            if not isinstance(codes, list) or not all(isinstance(code, str) and code for code in codes):
                raise ValueError("Preference codes must be text lists")
    if binding["template_id"] != template["template_id"]:
        raise ValueError("Context binding must match the template")
    blocked, missing = [], []
    category = place.get("activity_category")
    if category is None:
        missing.append("place_category_unknown")
    elif category not in binding["eligible_place_categories"]:
        blocked.append("place_category_excluded")
    if template["category"] != "any" and category is not None and category != template["category"]:
        blocked.append("template_category_excluded")
    # Only explicit boolean evidence counts. A park label or a non-empty string is not proof.
    features = place.get("confirmed_features", {})
    if features is None:
        features = {}
    if not isinstance(features, dict):
        raise ValueError("Confirmed features must be an object")
    for requirement in template["site_requirements"]:
        if features.get(requirement) is False:
            blocked.append("site_requirement_absent:" + requirement)
        elif features.get(requirement) is not True:
            missing.append("site_requirement_unknown:" + requirement)
    for field in ("weather_allowed", "air_quality_allowed"):
        if context.get(field) is False:
            blocked.append(field + ":false")
        elif context.get(field) is not True:
            missing.append(field + ":unknown")
    if "any" not in template["weather_tags"]:
        tags = context.get("weather_tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) for tag in tags):
            missing.append("weather_tags_unknown")
        elif not set(tags).intersection(template["weather_tags"]):
            blocked.append("weather_tag_mismatch")
    preference_match = None
    if preferences and any(preferences.values()):
        if preference_binding_status != "bound":
            missing.append("preference_codes_unbound")
        elif set(preferences.get("excluded_codes", [])).intersection(binding["preference_codes"]):
            blocked.append("preference_excluded")
        if preference_binding_status == "bound" and preferences.get("preferred_codes"):
            preference_match = bool(set(preferences["preferred_codes"]).intersection(binding["preference_codes"]))
    # Exclusions are separate from hard constraints; only Backend B may apply its relaxation policy.
    status = "excluded" if blocked else "needs_context" if missing else "candidate"
    return {"status": status, "blocked": blocked, "missing": missing, "preference_match": preference_match,
            "note": "Content candidate only; not approval, ranking or a deployed recommendation."}
