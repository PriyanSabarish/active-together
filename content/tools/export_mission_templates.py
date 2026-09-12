"""Export migrated families or one 3/5/7-step Mission in an explicit content envelope."""

import argparse
import json
from pathlib import Path
import sys

from jsonschema.exceptions import SchemaError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from content.tools.activity_library import AGE_BANDS, CONTENT_DIR
from content.tools.mission_context import load_context_bindings
from content.tools.mission_library import CONTRACT_VERSION, build_mission, load_mission_families


def build_export(preview=False, template_id=None, age_band=None, duration=None, content_dir=CONTENT_DIR):
    """Validate before exporting; include essential parent briefings outside the wire shape."""
    families, warnings = load_mission_families(preview, content_dir)
    config, bindings = load_context_bindings(families, content_dir)
    payload = {
        "contract_version": CONTRACT_VERSION,
        "mode": "development_preview" if preview else "reviewed",
        "duration_basis": "backend_step_count_contract_not_measured",
        "preference_binding_status": config["preference_binding_status"],
        "warnings": warnings,
    }
    if template_id is None:
        if age_band is not None or duration is not None:
            raise ValueError("Age and duration need an explicit template ID")
        payload["templates"] = families
        payload["content_bindings"] = [bindings[item["template_id"]] for item in families]
    else:
        template = next((item for item in families if item["template_id"] == template_id), None)
        if template is None:
            raise ValueError("Template unavailable in this mode: " + template_id)
        if age_band is None or duration is None:
            raise ValueError("A Mission export needs both age band and duration")
        payload["mission"] = build_mission(template, age_band, duration, content_dir)
        payload["content_binding"] = bindings[template_id]
    return payload


def main():
    """Print JSON or save a validated .json output without overwriting on invalid input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--template-id")
    parser.add_argument("--age-band", choices=AGE_BANDS)
    parser.add_argument("--duration", type=int, choices=(20, 40, 60))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.output.suffix.lower() != ".json":
            raise ValueError("Output must use a .json extension")
        payload = build_export(args.preview, args.template_id, args.age_band, args.duration)
        output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
            print("Wrote " + payload["mode"] + " to " + str(args.output))
        else:
            print(output, end="")
    except (OSError, ValueError, SchemaError) as error:
        parser.exit(1, f"Mission export failed: {error}\n")


if __name__ == "__main__":
    main()
