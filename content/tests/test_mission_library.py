"""Test mission migration, photo hooks, all safety rules and wire-format boundaries."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

from content.tools.activity_library import CONTENT_DIR, read_yaml
from content.tools.export_mission_templates import build_export
from content.tools.mission_checks import check_step_text, load_content_rules
from content.tools.mission_library import (
    build_mission, load_mission_families, load_mission_rules, validate_family, validate_mission,
)


class MissionLibraryTests(unittest.TestCase):
    """Keep all deliberately unsafe or fake-reviewed content in isolated test folders."""

    @classmethod
    def setUpClass(cls):
        """Read the authored families once for the suite."""
        cls.families, cls.warnings = load_mission_families(True)

    def setUp(self):
        """Copy required rules and a draft seed without altering real content."""
        self.temp = tempfile.TemporaryDirectory(prefix="mission_contract_")
        self.addCleanup(self.temp.cleanup)
        self.content = Path(self.temp.name)
        for folder in ("schema", "prompts", "taxonomy", "missions/_candidates", "missions/reviewed"):
            (self.content / folder).mkdir(parents=True, exist_ok=True)
        for path in ("schema/mission_family.validation.yaml", "schema/safety_constraints.yaml",
                     "schema/mission_context.validation.yaml", "prompts/vocabulary.yaml",
                     "taxonomy/mission_context_bindings.yaml", "taxonomy/activity_types.yaml"):
            shutil.copyfile(CONTENT_DIR / path, self.content / path)
        self.seed = copy.deepcopy(next(item for item in self.families
                                       if item["template_id"] == "activity_colour_hunt"))
        self.seed["review"] = {"author": "Jiabin", "reviewed_by": None, "status": "draft"}
        self.save(self.seed)

    def save(self, family, folder="_candidates", filename=None):
        """Write one isolated family fixture using the production wrapper."""
        path = self.content / "missions" / folder / (filename or family["template_id"] + ".yaml")
        path.write_text(yaml.safe_dump({"templates": [family]}, sort_keys=False), encoding="utf-8")
        return path

    def test_all_162_combinations_follow_the_wire_contract(self):
        """Keep every complete authored prefix and exclude authoring-only fields."""
        self.assertEqual(len(self.families), 18)
        self.assertEqual(self.warnings, [])
        combinations = 0
        for family in self.families:
            self.assertEqual(set(family["bands"]), {"5-7", "8-10", "11-12"})
            for band in family["bands"]:
                for duration, count in ((20, 3), (40, 5), (60, 7)):
                    with self.subTest(template=family["template_id"], band=band, duration=duration):
                        mission = build_mission(family, band, duration)
                        self.assertEqual(len(mission["steps"]), count)
                        self.assertEqual(mission["estimated_minutes"], duration)
                        for index, step in enumerate(mission["steps"]):
                            self.assertEqual(set(step), {"sequence", "prompt_text", "verify_mode", "prompt_id"})
                            self.assertEqual(step["prompt_text"], family["bands"][band]["steps"][index]["prompt_text"])
                        combinations += 1
        self.assertEqual(combinations, 162)

    def test_no_real_photo_prompt_is_claimed_as_measured(self):
        """The migration exposes hooks but does not fabricate measurement evidence."""
        for family in self.families:
            for band in family["bands"].values():
                for step in band["steps"]:
                    self.assertEqual(step["verify_mode"], "self")
                    self.assertIsNone(step["prompt_id"])

    def test_reviewed_mode_does_not_fall_back_to_drafts(self):
        """An empty approved collection stays empty, even with a malformed draft."""
        self.assertEqual(build_export(content_dir=self.content)["templates"], [])
        self.seed["unexpected"] = True
        self.save(self.seed)
        self.assertEqual(load_mission_families(False, self.content)[0], [])
        with self.assertRaises(ValueError):
            load_mission_families(True, self.content)

    def test_reviewed_export_contains_the_approved_migration(self):
        """Verify the completed eighteen-family review handoff and removal of draft copies."""
        payload = build_export()
        ids = {item["template_id"] for item in payload["templates"]}
        self.assertEqual(len(ids), 18)
        self.assertEqual(ids, {item["template_id"] for item in self.families})
        self.assertEqual(payload["mode"], "reviewed")
        for family in payload["templates"]:
            self.assertEqual(family["review"]["status"], "reviewed")
            self.assertEqual(family["review"]["reviewed_by"], "lychen")
            self.assertFalse((CONTENT_DIR / "missions/_candidates" / (family["template_id"] + ".yaml")).exists())

    def test_promotion_requires_an_independent_reviewer(self):
        """Exercise approved loading with an explicitly fictional test reviewer."""
        self.seed["review"] = {"author": "Jiabin", "reviewed_by": " JIABIN ", "status": "reviewed"}
        rules = load_mission_rules(self.content)
        with self.assertRaises(ValueError):
            validate_family(self.seed, rules)
        self.seed["review"]["reviewed_by"] = "Fixture reviewer"
        self.save(self.seed, "reviewed")
        (self.content / "missions/_candidates/activity_colour_hunt.yaml").unlink()
        approved, _ = load_mission_families(False, self.content)
        self.assertEqual(len(approved), 1)
        self.assertEqual(build_export(content_dir=self.content)["mode"], "reviewed")

    def test_duplicate_ids_and_filename_mismatch_fail(self):
        """Reject ambiguous identities rather than silently choosing a file."""
        self.save(self.seed, filename="activity_wrong.yaml")
        with self.assertRaises(ValueError):
            load_mission_families(True, self.content)
        (self.content / "missions/_candidates/activity_wrong.yaml").unlink()
        self.seed["review"] = {"author": "Jiabin", "reviewed_by": "Fixture reviewer", "status": "reviewed"}
        self.save(self.seed, "reviewed")
        with self.assertRaises(ValueError):
            load_mission_families(True, self.content)

    def test_photo_fields_and_vocabulary_are_enforced(self):
        """Only a fixture-local kept prompt enables the positive photo test."""
        photo = read_yaml(CONTENT_DIR / "tests/fixtures/photo_family.yaml")
        rules = load_mission_rules(self.content)
        with self.assertRaises(ValueError):
            validate_family(photo, rules)
        vocab = read_yaml(self.content / "prompts/vocabulary.yaml")
        next(item for item in vocab["prompts"] if item["id"] == "p_red")["status"] = "kept"
        (self.content / "prompts/vocabulary.yaml").write_text(yaml.safe_dump(vocab), encoding="utf-8")
        rules = load_mission_rules(self.content)
        self.assertEqual(validate_family(photo, rules), [])
        mission = build_mission(photo, "5-7", 20, self.content)
        self.assertEqual(mission["steps"][0]["verify_mode"], "photo")
        self.assertTrue(validate_mission(mission, photo, self.content)["ok"])
        for changes in ({"prompt_id": None}, {"prompt_id": "unknown"},
                        {"verify_mode": "self"}, {"verify_mode": "video"}):
            invalid = copy.deepcopy(photo)
            invalid["bands"]["5-7"]["steps"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_family(invalid, rules)
        dropped = dict(rules[2], p_red=dict(rules[2]["p_red"], status="dropped"))
        with self.assertRaises(ValueError):
            validate_family(photo, (rules[0], rules[1], dropped))

    def test_all_nine_constraints_reject_authored_and_rewritten_steps(self):
        """Golden rejection cases run before any generator or model service exists."""
        cases = read_yaml(CONTENT_DIR / "tests/fixtures/mission_rejections.yaml")["cases"]
        constraints, _ = load_content_rules(self.content)
        self.assertEqual({item["rule_id"] for item in cases}, {item["id"] for item in constraints})
        rules = load_mission_rules(self.content)
        for case in cases:
            with self.subTest(rule=case["rule_id"]):
                invalid = copy.deepcopy(self.seed)
                invalid["bands"]["5-7"]["steps"][0]["prompt_text"] = case["prompt_text"]
                with self.assertRaisesRegex(ValueError, case["rule_id"]):
                    validate_family(invalid, rules)
                mission = build_mission(self.seed, "5-7", 20, self.content)
                mission["steps"][0]["prompt_text"] = case["prompt_text"]
                result = validate_mission(mission, self.seed, self.content)
                self.assertFalse(result["ok"])
                self.assertIn(case["rule_id"], " ".join(result["failures"]))

    def test_actual_rule_file_is_loaded_and_missing_rules_fail(self):
        """A changed reject list affects validation, while incomplete rule files fail closed."""
        safety_path = self.content / "schema/safety_constraints.yaml"
        safety = read_yaml(safety_path)
        safety["constraints"][0]["rejects"].append("fixture forbidden action")
        safety_path.write_text(yaml.safe_dump(safety), encoding="utf-8")
        self.seed["bands"]["5-7"]["steps"][0]["prompt_text"] = "Try the fixture forbidden action."
        with self.assertRaisesRegex(ValueError, "no_climbing"):
            validate_family(self.seed, load_mission_rules(self.content))
        safety["constraints"].pop()
        safety_path.write_text(yaml.safe_dump(safety), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_mission_rules(self.content)
        safety_path.unlink()
        with self.assertRaises(ValueError):
            load_mission_rules(self.content)

    def test_phrase_boundaries_variants_filler_and_invention(self):
        """Catch hazards across punctuation without substring errors in ordinary words."""
        constraints, _ = load_content_rules(self.content)
        for text in ("Repeat the rhythm with your signal.", "Choose a design together."):
            self.assertEqual(check_step_text(text, constraints), ([], []))
        for text in ("Try climbing now.", "Start digging here.", "Cross-the-road.", "Go OUT OF SIGHT."):
            self.assertTrue(check_step_text(text, constraints)[0])
        self.assertTrue(check_step_text("Give a big smile.", constraints)[0])
        self.assertTrue(check_step_text("Walk to the painted line.", constraints)[1])
        mission = build_mission(self.seed, "5-7", 20, self.content)
        mission["steps"][0]["prompt_text"] = "Walk to the painted line."
        self.assertFalse(validate_mission(mission, self.seed, self.content)["ok"])

    def test_malformed_families_and_unavailable_requests_fail(self):
        """Check sequence, types, age limits, missing fields and exact bucket selection."""
        rules = load_mission_rules(self.content)
        for key, value in (("sequence", 2), ("prompt_id", "p_red"), ("variable", False),
                           ("prompt_text", "one two three four five six seven eight nine ten eleven twelve")):
            invalid = copy.deepcopy(self.seed)
            invalid["bands"]["5-7"]["steps"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_family(invalid, rules)
        for band, minutes in (("13-15", 20), ("5-7", 90), ("5-7", True), ("5-7", "20")):
            with self.assertRaises(ValueError):
                build_mission(self.seed, band, minutes, self.content)
        invalid = copy.deepcopy(self.seed)
        invalid["bands"]["8-10"] = copy.deepcopy(invalid["bands"]["5-7"])
        with self.assertRaises(ValueError):
            validate_family(invalid, rules)

    def test_final_mission_contract_is_not_silently_changed(self):
        """Reject malformed rewrites and altered verification targets or equipment."""
        base = build_mission(self.seed, "5-7", 20, self.content)
        for field, value in (("age_band", []), ("equipment", ["ball"]),
                             ("estimated_minutes", 60), ("title", ""), ("title", "Cross the road"), ("steps", None)):
            mission = copy.deepcopy(base)
            mission[field] = value
            with self.subTest(field=field):
                self.assertFalse(validate_mission(mission, self.seed, self.content)["ok"])
        mission = copy.deepcopy(base)
        mission["steps"][0]["verify_mode"] = "photo"
        mission["steps"][0]["prompt_id"] = "p_red"
        self.assertFalse(validate_mission(mission, self.seed, self.content)["ok"])

    def test_cli_and_generated_examples(self):
        """Run the public tools outside the repository and compare checked-in JSON."""
        result = subprocess.run([sys.executable, str(CONTENT_DIR / "tools/validate_mission_templates.py"),
                                 "--preview"], cwd=self.content, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("18 families, 54 age variants, 162", result.stdout)
        result = subprocess.run([sys.executable, str(CONTENT_DIR / "tools/export_mission_templates.py"),
                                 "--preview", "--template-id", "activity_colour_hunt", "--age-band", "5-7",
                                 "--duration", "20"], cwd=self.content, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = build_export(True, "activity_colour_hunt", "5-7", 20)
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(json.loads((CONTENT_DIR / "examples/mission.preview.json").read_text(encoding="utf-8")), expected)
        self.assertEqual(json.loads((CONTENT_DIR / "examples/mission_families.preview.json").read_text(encoding="utf-8")), build_export(True))
        self.assertEqual(json.loads((CONTENT_DIR / "examples/mission_families.reviewed.json").read_text(encoding="utf-8")), build_export())

    def test_invalid_export_preserves_existing_output(self):
        """A failed lookup must not erase a previously generated artifact."""
        output = self.content / "existing.json"
        output.write_text("keep this", encoding="utf-8")
        result = subprocess.run([sys.executable, str(CONTENT_DIR / "tools/export_mission_templates.py"),
                                 "--template-id", "activity_missing_test_fixture", "--age-band", "5-7", "--duration", "20",
                                 "--output", str(output)], cwd=self.content, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep this")


if __name__ == "__main__":
    unittest.main()
