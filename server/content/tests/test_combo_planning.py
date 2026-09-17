"""Check draft duration arithmetic, reference boundaries and generated reports."""

import copy
import json
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator

from content.tools.activity_library import CONTENT_DIR, load_preview_activities, read_yaml
from content.tools.combo_planning import build_combo_preview, load_duration_rules, validate_profiles
from content.tools.report_activity_coverage import build_coverage_report


class ComboPlanningTests(unittest.TestCase):
    """Exercise estimates without treating them as approved runtime recommendations."""

    def test_exact_fit_and_bounded_extensions(self):
        """Optional authored rounds may fill a budget but must respect their caps."""
        plan = build_combo_preview(["rhythm_steps", "colour_hunt"], "5-7", 20)
        self.assertEqual(plan["status"], "fits_estimate")
        self.assertEqual(plan["scheduled_minutes"], 20)
        self.assertEqual(plan["unused_minutes"], 0)
        config, profiles = load_duration_rules(load_preview_activities())
        for block in plan["blocks"]:
            if block["kind"] == "activity":
                profile = profiles[block["activity_id"]]
                self.assertLessEqual(block["extra_rounds"], profile["max_extra_rounds"])
                self.assertEqual(block["minutes"], block["base_minutes"] + block["extra_rounds"] * profile["extension_minutes"])

    def test_long_budget_preserves_unused_time(self):
        """A longer request does not stretch activities or silently invent filler."""
        plan = build_combo_preview(["follow_the_leader", "colour_hunt", "pass_and_move"], "8-10", 60)
        self.assertEqual(plan["status"], "unused_time")
        self.assertEqual(plan["scheduled_minutes"], 48)
        self.assertEqual(plan["unused_minutes"], 12)
        self.assertEqual(sum(block["minutes"] for block in plan["blocks"]), 48)
        self.assertEqual(plan["mode"], "development_preview")
        self.assertEqual(plan["timing_basis"], "author_estimate_not_measured")

    def test_over_budget_does_not_cut_core_activities(self):
        """Core durations remain intact when the chosen pair cannot fit."""
        plan = build_combo_preview(["sort_and_step", "imaginary_delivery"], "11-12", 20)
        self.assertEqual(plan["status"], "over_budget")
        self.assertEqual(plan["scheduled_minutes"], 21)
        self.assertEqual(plan["over_budget_minutes"], 1)
        self.assertEqual(plan["unused_minutes"], 0)
        self.assertTrue(all(block["extra_rounds"] == 0 for block in plan["blocks"] if block["kind"] == "activity"))

    def test_invalid_choices_fail(self):
        """Reject duplicates, unavailable content, wrong counts, ages and budgets."""
        cases = [
            (["colour_hunt", "colour_hunt"], "5-7", 20),
            (["colour_hunt", "missing"], "5-7", 20),
            (["colour_hunt"], "5-7", 20),
            (["colour_hunt", "follow_the_leader"], "13-15", 20),
            (["colour_hunt", "follow_the_leader"], "5-7", 90),
        ]
        for ids, band, minutes in cases:
            with self.subTest(ids=ids, band=band, minutes=minutes):
                with self.assertRaises(ValueError):
                    build_combo_preview(ids, band, minutes)

    def test_profiles_reject_stale_or_incomplete_references(self):
        """Every estimate must reference the current activity, supported ages and extension."""
        activities = load_preview_activities()
        config, profiles = load_duration_rules(activities)
        self.assertEqual(len(profiles), 18)
        cases = []
        for field, value in (("activity_id", "unknown"), ("activity_version", 999),
                             ("extension_index", 999), ("base_minutes", {"5-7": 3})):
            invalid = copy.deepcopy(config["activity_profiles"])
            invalid[0][field] = value
            cases.append(invalid)
        cases.append(config["activity_profiles"][:-1])
        cases.append(config["activity_profiles"] + [config["activity_profiles"][0]])
        for index, invalid in enumerate(cases):
            with self.subTest(case=index):
                with self.assertRaises(ValueError):
                    validate_profiles(invalid, activities)

    def test_timing_schema_rejects_invalid_numbers_and_approval(self):
        """Draft estimates cannot claim reviewed status or accept invalid durations."""
        schema = read_yaml(CONTENT_DIR / "schema/duration_profiles.schema.yaml")
        validator = Draft202012Validator(schema)
        config = read_yaml(CONTENT_DIR / "planning/duration_profiles.yaml")
        invalid = copy.deepcopy(config)
        invalid["status"] = "reviewed"
        self.assertFalse(validator.is_valid(invalid))
        for value in (-1, True, 2.5):
            invalid = copy.deepcopy(config)
            invalid["activity_profiles"][0]["base_minutes"]["5-7"] = value
            self.assertFalse(validator.is_valid(invalid))

    def test_examples_and_coverage_are_current(self):
        """Keep generated evidence synchronized and show the deferred content gaps."""
        example = json.loads((CONTENT_DIR / "examples/combo.preview.json").read_text(encoding="utf-8"))
        self.assertEqual(example, build_combo_preview(["follow_the_leader", "colour_hunt", "pass_and_move"], "8-10", 40))
        report = build_coverage_report()
        self.assertEqual(report, (CONTENT_DIR / "activities/COVERAGE.md").read_text(encoding="utf-8"))
        self.assertIn("18 activities; 54 age variants", report)
        self.assertIn("racket_play, wheeled_play", report)
        self.assertIn("21 source places", report)

    def test_preview_cli_runs_outside_repository(self):
        """Check that the direct CLI resolves content relative to its own file."""
        result = subprocess.run([
            sys.executable, str(CONTENT_DIR / "tools/plan_combo_preview.py"),
            "--duration", "20", "--age-band", "5-7", "--activity-id", "rhythm_steps",
            "--activity-id", "colour_hunt",
        ], cwd=CONTENT_DIR.parent.parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "fits_estimate")


if __name__ == "__main__":
    unittest.main()
