"""Check activity loading boundaries and the sample integration contract."""

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from content.tools.activity_library import (
    CONTENT_DIR,
    build_export,
    load_preview_activities,
    load_reviewed_activities,
    read_yaml,
    select_activities,
)


class ActivityLibraryTests(unittest.TestCase):
    """Use isolated content folders so the real activity library stays untouched."""

    def setUp(self):
        """Copy the contract and one draft into a temporary content library."""
        self.temp = tempfile.TemporaryDirectory(prefix="activity_library_")
        self.addCleanup(self.temp.cleanup)
        self.content = Path(self.temp.name)
        for folder in ("schema", "taxonomy", "activities/_candidates", "activities/reviewed"):
            (self.content / folder).mkdir(parents=True, exist_ok=True)
        for relative in ("schema/activity_template.schema.yaml", "taxonomy/activity_types.yaml"):
            shutil.copyfile(CONTENT_DIR / relative, self.content / relative)
        self.sample = read_yaml(CONTENT_DIR / "activities/_candidates/follow_the_leader.yaml")
        self.save(self.sample)

    def save(self, activity, folder="_candidates", filename="follow_the_leader.yaml"):
        """Write a test record to the isolated library and return its path."""
        path = self.content / "activities" / folder / filename
        path.write_text(yaml.safe_dump(activity, sort_keys=False), encoding="utf-8")
        return path

    def run_cli(self, script, *arguments):
        """Run a real CLI outside the repository and capture its output."""
        return subprocess.run(
            [sys.executable, str(CONTENT_DIR / "tools" / script), *arguments],
            cwd=self.content, capture_output=True, text=True, encoding="utf-8",
        )

    def test_samples_and_generated_preview_agree(self):
        """Keep the checked-in JSON synchronized with all three YAML samples."""
        payload = build_export(preview=True)
        expected_ids = ["colour_hunt", "follow_the_leader", "pass_and_move"]
        self.assertEqual([item["activity_id"] for item in payload["activities"]], expected_ids)
        self.assertEqual(sum(len(item["age_variants"]) for item in payload["activities"]), 9)
        exported = json.loads((CONTENT_DIR / "examples/activities.preview.json").read_text(encoding="utf-8"))
        self.assertEqual(payload, exported)
        self.assertTrue(all(item["review"]["author"] == "Jiabin" for item in payload["activities"]))
        ball = next(item for item in payload["activities"] if item["activity_type"] == "ball_play")
        self.assertTrue(ball["equipment"]["required"])

    def test_reviewed_mode_never_falls_back_to_drafts(self):
        """Empty reviewed content stays empty even when drafts are available."""
        self.assertEqual(load_reviewed_activities(self.content), [])
        self.assertEqual(len(load_preview_activities(self.content)), 1)
        self.assertEqual(build_export(content_dir=self.content), {
            "schema_version": "0.1.0", "mode": "reviewed", "activities": [],
        })

    def test_bad_draft_does_not_affect_reviewed_loading(self):
        """Reviewed loading does not read candidates; preview reports their errors."""
        path = self.content / "activities/_candidates/follow_the_leader.yaml"
        path.write_text("title: [broken", encoding="utf-8")
        self.assertEqual(load_reviewed_activities(self.content), [])
        with self.assertRaises(ValueError):
            load_preview_activities(self.content)

    def test_reviewed_record_loads_after_promotion(self):
        """An independently reviewed test fixture can enter the reviewed folder."""
        self.sample["review"] = {"author": "Jiabin", "reviewed_by": "Test Reviewer", "status": "reviewed"}
        self.save(self.sample, folder="reviewed")
        (self.content / "activities/_candidates/follow_the_leader.yaml").unlink()
        self.assertEqual(len(load_reviewed_activities(self.content)), 1)

    def test_review_violations_are_rejected(self):
        """Reject drafts in reviewed, missing reviewers, self-review and stale draft review."""
        cases = [
            ("reviewed", {"author": "Jiabin", "reviewed_by": None, "status": "draft"}),
            ("reviewed", {"author": "Jiabin", "reviewed_by": None, "status": "reviewed"}),
            ("reviewed", {"author": "Jiabin", "reviewed_by": "  JIABIN ", "status": "reviewed"}),
            ("_candidates", {"author": "Jiabin", "reviewed_by": "Test Reviewer", "status": "draft"}),
            ("_candidates", {"author": "Jiabin", "reviewed_by": "Test Reviewer", "status": "reviewed"}),
        ]
        for folder, review in cases:
            with self.subTest(folder=folder, review=review):
                invalid = copy.deepcopy(self.sample)
                invalid["review"] = review
                path = self.save(invalid, folder=folder)
                with self.assertRaises(ValueError):
                    load_preview_activities(self.content)
                path.unlink()

    def test_schema_and_reference_errors_are_rejected(self):
        """Catch malformed records and content references not covered by JSON Schema."""
        cases = []
        for field, value in (("activity_type", "unknown"), ("core_mechanic", "unknown"),
                             ("title", " "), ("version", 0), ("duration_bucket", 20)):
            invalid = copy.deepcopy(self.sample)
            invalid[field] = value
            cases.append(invalid)
        invalid = copy.deepcopy(self.sample)
        del invalid["equipment"]
        cases.append(invalid)
        invalid = copy.deepcopy(self.sample)
        invalid["age_variants"]["5-7"]["steps"] = []
        cases.append(invalid)
        invalid = copy.deepcopy(self.sample)
        invalid["age_variants"]["5-7"]["steps"][1]["step_id"] = "copy_one"
        cases.append(invalid)
        invalid = copy.deepcopy(self.sample)
        invalid["age_variants"]["13-15"] = invalid["age_variants"].pop("11-12")
        cases.append(invalid)
        for index, invalid in enumerate(cases):
            with self.subTest(case=index):
                self.save(invalid)
                with self.assertRaises(ValueError):
                    load_preview_activities(self.content)

    def test_duplicate_yaml_fields_are_rejected(self):
        """A repeated YAML field must not silently replace its earlier value."""
        path = self.content / "activities/_candidates/follow_the_leader.yaml"
        path.write_text("title: first\ntitle: second\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Repeated YAML field"):
            load_preview_activities(self.content)

    def test_duplicate_ids_and_filename_mismatch_are_rejected(self):
        """Catch duplicate records across folders and misleading filenames."""
        approved = copy.deepcopy(self.sample)
        approved["review"] = {"author": "Jiabin", "reviewed_by": "Test Reviewer", "status": "reviewed"}
        path = self.save(approved, folder="reviewed")
        with self.assertRaisesRegex(ValueError, "Duplicate activity_id"):
            load_preview_activities(self.content)
        path.unlink()
        self.save(self.sample, filename="wrong_name.yaml")
        with self.assertRaisesRegex(ValueError, "filename must match"):
            load_preview_activities(self.content)

    def test_type_and_age_filtering_preserve_records(self):
        """Select exactly the requested type and age without flattening the data."""
        activities = load_preview_activities()
        selected = select_activities(activities, "ball_play", "8-10")
        self.assertEqual([item["activity_id"] for item in selected], ["pass_and_move"])
        self.assertEqual(len(selected[0]["age_variants"]), 3)
        self.assertEqual(select_activities(activities, "unknown"), [])
        with self.assertRaises(ValueError):
            select_activities(activities, age_band="13-15")

    def test_missing_age_does_not_substitute_another_band(self):
        """A valid but unwritten age variant returns no match."""
        del self.sample["age_variants"]["11-12"]
        self.save(self.sample)
        activities = load_preview_activities(self.content)
        self.assertEqual(select_activities(activities, age_band="11-12"), [])
        self.assertEqual(len(select_activities(activities, age_band="5-7")), 1)

    def test_invalid_content_fails_before_filtering(self):
        """An unmatched type filter must not hide a broken activity."""
        del self.sample["equipment"]
        self.save(self.sample)
        with self.assertRaises(ValueError):
            build_export(preview=True, activity_type="racket_play", content_dir=self.content)

    def test_cli_modes_filters_and_output(self):
        """Exercise stdout JSON and explicit file export from another directory."""
        result = self.run_cli("export_activity_templates.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["mode"], "reviewed")
        result = self.run_cli("export_activity_templates.py", "--preview", "--age-band", "8-10", "--activity-type", "ball_play")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "development_preview")
        self.assertEqual(len(payload["activities"]), 1)
        output = self.content / "export.json"
        result = self.run_cli("export_activity_templates.py", "--preview", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(output.read_text(encoding="utf-8"))["activities"]), 3)
        result = self.run_cli("validate_activity_templates.py", "--preview")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3 activities, 9 age variants", result.stdout)

    def test_invalid_cli_request_preserves_existing_output(self):
        """An invalid argument cannot overwrite an existing output file."""
        output = self.content / "existing.json"
        output.write_text("keep me", encoding="utf-8")
        result = self.run_cli("export_activity_templates.py", "--age-band", "13-15", "--output", str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep me")


if __name__ == "__main__":
    unittest.main()
