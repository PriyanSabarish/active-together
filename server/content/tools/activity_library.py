"""Load activity records for reviewed use or explicit development preview."""

from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


CONTENT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1.0"
AGE_BANDS = ("5-7", "8-10", "11-12")


class ActivityLoader(yaml.SafeLoader):
    """Read safe YAML and reject duplicate or non-text field names."""


def unique_mapping(loader, node):
    """Build a YAML object without silently replacing a repeated field."""
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("YAML field names must be text; quote age-band keys.")
        if key in result:
            raise ValueError("Repeated YAML field: " + key)
        result[key] = loader.construct_object(value_node)
    return result


ActivityLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping,
)


def read_yaml(path):
    """Read one UTF-8 YAML file and include its path in any error."""
    path = Path(path)
    try:
        return yaml.load(path.read_text(encoding="utf-8-sig"), Loader=ActivityLoader)
    except (OSError, yaml.YAMLError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error


def load_rules(content_dir):
    """Read the activity schema and the permitted type and mechanic IDs."""
    schema = read_yaml(content_dir / "schema/activity_template.schema.yaml")
    Draft202012Validator.check_schema(schema)
    taxonomy = read_yaml(content_dir / "taxonomy/activity_types.yaml")
    if not isinstance(taxonomy, dict) or taxonomy.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Activity taxonomy has an unsupported schema version.")
    entries = taxonomy.get("activity_types", [])
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise ValueError("Activity taxonomy must contain a list of type records.")
    activity_types = [item.get("id") for item in entries]
    mechanics = taxonomy.get("core_mechanics")
    for name, values in (("activity types", activity_types), ("mechanics", mechanics)):
        if not isinstance(values, list) or not values:
            raise ValueError(f"Taxonomy {name} must be a non-empty list.")
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError(f"Taxonomy {name} must contain text IDs.")
        if len(values) != len(set(values)):
            raise ValueError(f"Taxonomy {name} contains duplicate IDs.")
    return Draft202012Validator(schema), activity_types, mechanics


def validate_activity(activity, path, validator, activity_types, mechanics, status):
    """Check structure, references, step IDs and the folder's review rules."""
    error = next(validator.iter_errors(activity), None)
    if error:
        field = ".".join(str(part) for part in error.absolute_path) or "record"
        raise ValueError(f"{path.name}: {field}: {error.message}")
    if activity["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"{path.name}: unsupported activity schema version.")
    if path.stem != activity["activity_id"]:
        raise ValueError(f"{path.name}: filename must match activity_id.")
    if activity["activity_type"] not in activity_types:
        raise ValueError(f"{path.name}: unknown activity_type.")
    if activity["core_mechanic"] not in mechanics:
        raise ValueError(f"{path.name}: unknown core_mechanic.")
    for band, variant in activity["age_variants"].items():
        ids = [step["step_id"] for step in variant["steps"]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{path.name}: repeated step_id in age band {band}.")
    review = activity["review"]
    if review["status"] != status:
        raise ValueError(f"{path.name}: this folder requires review.status: {status}.")
    if status == "draft" and review["reviewed_by"] is not None:
        raise ValueError(f"{path.name}: a draft must have reviewed_by: null.")
    if status == "reviewed":
        author = " ".join(review["author"].split()).casefold()
        reviewer = " ".join(review["reviewed_by"].split()).casefold()
        if author == reviewer:
            raise ValueError(f"{path.name}: author and reviewer must be different people.")


def load_folders(content_dir, folders):
    """Validate every selected file before returning a sorted activity list."""
    content_dir = Path(content_dir)
    validator, activity_types, mechanics = load_rules(content_dir)
    activities = []
    seen_ids = set()
    for folder_name, status in folders:
        folder = content_dir / "activities" / folder_name
        if not folder.is_dir():
            raise ValueError(f"Activity folder does not exist: {folder}")
        # Read both common YAML suffixes; the authoring convention uses .yaml.
        paths = sorted(list(folder.glob("*.yaml")) + list(folder.glob("*.yml")))
        for path in paths:
            activity = read_yaml(path)
            validate_activity(activity, path, validator, activity_types, mechanics, status)
            if activity["activity_id"] in seen_ids:
                raise ValueError("Duplicate activity_id: " + activity["activity_id"])
            seen_ids.add(activity["activity_id"])
            activities.append(activity)
    return sorted(activities, key=lambda activity: activity["activity_id"])


def load_reviewed_activities(content_dir=CONTENT_DIR):
    """Load only approved records; never fall back to draft content."""
    return load_folders(content_dir, [("reviewed", "reviewed")])


def load_preview_activities(content_dir=CONTENT_DIR):
    """Load reviewed records and drafts for development testing only."""
    return load_folders(content_dir, [("reviewed", "reviewed"), ("_candidates", "draft")])


def select_activities(activities, activity_type=None, age_band=None):
    """Filter by exact type and supported age; preserve complete records."""
    if age_band is not None and age_band not in AGE_BANDS:
        raise ValueError("Unsupported age band; use 5-7, 8-10 or 11-12.")
    selected = []
    for activity in activities:
        if activity_type is not None and activity["activity_type"] != activity_type:
            continue
        if age_band is not None and age_band not in activity["age_variants"]:
            continue
        selected.append(activity)
    return selected


def build_export(preview=False, activity_type=None, age_band=None, content_dir=CONTENT_DIR):
    """Build the JSON envelope, identifying whether drafts are allowed."""
    if preview:
        activities = load_preview_activities(content_dir)
    else:
        activities = load_reviewed_activities(content_dir)
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "development_preview" if preview else "reviewed",
        "activities": select_activities(activities, activity_type, age_band),
    }
