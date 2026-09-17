"""Load the migrated mission families and build Priyan's 3/5/7-step preview shape."""

import copy
from pathlib import Path

from jsonschema import Draft202012Validator

from content.tools.activity_library import AGE_BANDS, CONTENT_DIR, read_yaml
from content.tools.mission_checks import check_step_text, check_steps, load_content_rules


STEPS_FOR = {20: 3, 40: 5, 60: 7}
CONTRACT_VERSION = "1.0.0"


def load_mission_rules(content_dir=CONTENT_DIR):
    """Load the executable family schema, safety constraints and photo vocabulary."""
    content_dir = Path(content_dir)
    schema = read_yaml(content_dir / "schema/mission_family.validation.yaml")
    Draft202012Validator.check_schema(schema)
    constraints, prompts = load_content_rules(content_dir)
    return Draft202012Validator(schema), constraints, prompts


def validate_family(family, rules, expected_status=None):
    """Validate one full family and return non-blocking author-review warnings."""
    validator, constraints, prompts = rules
    error = next(validator.iter_errors(family), None)
    if error:
        field = ".".join(str(item) for item in error.absolute_path) or "family"
        raise ValueError(field + ": " + error.message)
    template_id = family["template_id"]
    review = family["review"]
    if expected_status and review["status"] != expected_status:
        raise ValueError(template_id + ": review status conflicts with folder")
    author = " ".join(review["author"].split()).casefold()
    reviewer = " ".join((review["reviewed_by"] or "").split()).casefold()
    if review["status"] == "draft" and review["reviewed_by"] is not None:
        raise ValueError(template_id + ": draft reviewer must be null")
    if review["status"] == "reviewed" and (not reviewer or reviewer == author):
        raise ValueError(template_id + ": independent reviewer required")
    if "any" in family["weather_tags"] and len(family["weather_tags"]) != 1:
        raise ValueError(template_id + ": any weather tag must stand alone")
    errors, warnings, band_texts = [], [], []
    titles = [family["title"]] + [item["title"] for item in family["bands"].values() if item["title"]]
    for title in titles:
        title_errors, title_warnings = check_step_text(title, constraints)
        errors.extend("title: " + message for message in title_errors)
        warnings.extend("title: " + message for message in title_warnings)
    for band, variant in family["bands"].items():
        steps = variant["steps"]
        if len(steps) != STEPS_FOR[family["duration_bucket"]]:
            errors.append(band + ": wrong step count for the longest bucket")
        failures, notices = check_steps(steps, band, constraints, prompts)
        errors.extend(failures)
        warnings.extend(notices)
        texts = tuple(" ".join(step["prompt_text"].casefold().split()) for step in steps)
        if len(set(texts)) != len(texts):
            errors.append(band + ": exact repeated step text")
        if texts in band_texts:
            errors.append(band + ": age bands have identical instructions")
        band_texts.append(texts)
    if errors:
        raise ValueError(template_id + ": " + "; ".join(errors))
    return [template_id + ": " + warning for warning in warnings]


def load_mission_families(preview=False, content_dir=CONTENT_DIR):
    """Load only activity_*.yaml in the migration collection; never serve old drafts."""
    content_dir = Path(content_dir)
    rules = load_mission_rules(content_dir)
    folders = [("reviewed", "reviewed")]
    if preview:
        folders.append(("_candidates", "draft"))
    families, warnings, seen, shapes = [], [], set(), set()
    for folder, status in folders:
        directory = content_dir / "missions" / folder
        if not directory.is_dir():
            raise ValueError("Missing mission folder: " + str(directory))
        paths = sorted(list(directory.glob("activity_*.yaml")) + list(directory.glob("activity_*.yml")))
        for path in paths:
            document = read_yaml(path)
            if (not isinstance(document, dict) or set(document) != {"templates"}
                    or not isinstance(document["templates"], list) or len(document["templates"]) != 1):
                raise ValueError(str(path) + ": expected one family under templates")
            family = document["templates"][0]
            warnings.extend(validate_family(family, rules, status))
            template_id = family["template_id"]
            if path.stem != template_id or template_id in seen:
                raise ValueError(template_id + ": duplicate ID or filename mismatch")
            seen.add(template_id)
            shape = tuple(tuple(step["prompt_text"].casefold() for step in family["bands"][band]["steps"])
                          for band in AGE_BANDS if band in family["bands"])
            if shape in shapes:
                raise ValueError(template_id + ": duplicates another complete family")
            shapes.add(shape)
            families.append(family)
    return sorted(families, key=lambda item: item["template_id"]), warnings


def validate_mission(mission, template, content_dir=CONTENT_DIR):
    """Check final wire steps against their family, including text after a rewrite."""
    rules = load_mission_rules(content_dir)
    validate_family(template, rules)
    failures = []
    fields = {"mission_id", "template_id", "title", "age_band", "estimated_minutes", "equipment", "steps"}
    if not isinstance(mission, dict) or set(mission) != fields:
        return {"ok": False, "failures": ["Mission fields do not match the wire contract"], "warnings": []}
    band, minutes = mission["age_band"], mission["estimated_minutes"]
    if (not isinstance(band, str) or band not in template["bands"] or type(minutes) is not int
            or minutes not in STEPS_FOR or minutes > template["duration_bucket"]):
        return {"ok": False, "failures": ["Unsupported mission age or duration"], "warnings": []}
    if mission["template_id"] != template["template_id"] or mission["equipment"] != template["equipment"]:
        failures.append("Mission changed template identity or equipment")
    if not all(isinstance(mission[key], str) and mission[key].strip() for key in ("mission_id", "title")):
        failures.append("Mission ID and title must be non-empty text")
    steps = mission["steps"]
    if not isinstance(steps, list) or len(steps) != STEPS_FOR[minutes]:
        return {"ok": False, "failures": failures + ["Wrong mission step count"], "warnings": []}
    # Reuse the family schema by restoring the authored variable flag (not a wire field).
    probe = copy.deepcopy(template)
    if not isinstance(mission["title"], str) or not mission["title"].strip():
        return {"ok": False, "failures": failures, "warnings": []}
    probe["title"] = mission["title"]
    probe["duration_bucket"] = minutes
    probe["bands"] = {band: {"title": None, "steps": []}}
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) != {"sequence", "prompt_text", "verify_mode", "prompt_id"}:
            return {"ok": False, "failures": failures + ["Malformed wire Step"], "warnings": []}
        original = template["bands"][band]["steps"][index]
        if any(step[key] != original[key] for key in ("sequence", "verify_mode", "prompt_id")):
            failures.append(f"Step {index + 1} changed order or verification target")
        probe["bands"][band]["steps"].append(dict(step, variable=True))
    try:
        warnings = validate_family(probe, rules)
        if warnings:
            failures.append("Final mission contains an unverified facility reference")
    except ValueError as error:
        failures.append(str(error))
        warnings = []
    return {"ok": not failures, "failures": failures, "warnings": warnings}


def build_mission(template, band, duration_bucket, content_dir=CONTENT_DIR):
    """Build and recheck the exact 3/5/7-step library shape; this does not approve drafts."""
    validate_family(template, load_mission_rules(content_dir))
    if not isinstance(band, str) or band not in template["bands"]:
        raise ValueError("Requested age band is unavailable; never substitute another band")
    if (type(duration_bucket) is not int or duration_bucket not in STEPS_FOR
            or duration_bucket > template["duration_bucket"]):
        raise ValueError("Requested duration is unavailable")
    variant = template["bands"][band]
    steps = [{key: value for key, value in step.items() if key != "variable"}
             for step in variant["steps"][:STEPS_FOR[duration_bucket]]]
    mission = {
        "mission_id": f"preview_{template['template_id']}_{band}_{duration_bucket}",
        "template_id": template["template_id"], "title": variant["title"] or template["title"],
        "age_band": band, "estimated_minutes": duration_bucket,
        "equipment": list(template["equipment"]), "steps": steps,
    }
    result = validate_mission(mission, template, content_dir)
    if not result["ok"]:
        raise ValueError("Built mission failed checks: " + "; ".join(result["failures"]))
    return mission
