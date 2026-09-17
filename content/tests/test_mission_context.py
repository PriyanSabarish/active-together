"""Exercise future context seams with synthetic normalized inputs, never live user data."""

import copy
import unittest

from content.tools.mission_context import assess_conditions, load_context_bindings
from content.tools.mission_library import load_mission_families


class MissionContextTests(unittest.TestCase):
    """Distinguish a missing fact, an exclusion and a content candidate."""

    def setUp(self):
        """Use one real family and synthetic positive feature evidence."""
        families, _ = load_mission_families(True)
        self.config, bindings = load_context_bindings(families)
        self.family = next(item for item in families if item["template_id"] == "activity_colour_hunt")
        self.binding = bindings[self.family["template_id"]]
        self.place = {"activity_category": "park_and_garden",
                      "confirmed_features": {"bare_site": True, "open_space": True}}
        self.context = {"weather_allowed": True, "air_quality_allowed": True, "weather_tags": ["dry"]}

    def test_all_families_have_unbound_preference_hooks(self):
        """Never claim invented preference codes are already supported by the client."""
        self.assertEqual(self.config["preference_binding_status"], "unbound")
        self.assertEqual(len(self.config["templates"]), 18)
        self.assertTrue(all(not item["preference_codes"] for item in self.config["templates"]))

    def test_positive_context_only_means_candidate(self):
        """Known positive context is still not content approval or a recommendation."""
        result = assess_conditions(self.family, self.binding, self.place, self.context)
        self.assertEqual(result["status"], "candidate")
        self.assertIn("not approval", result["note"])

    def test_place_category_is_not_feature_evidence(self):
        """A park label and truthy strings cannot prove usable space."""
        for features in ({}, {"bare_site": "yes", "open_space": "true"}):
            place = dict(self.place, confirmed_features=features)
            self.assertEqual(assess_conditions(self.family, self.binding, place, self.context)["status"], "needs_context")
        place = dict(self.place, confirmed_features={"bare_site": True, "open_space": False})
        self.assertEqual(assess_conditions(self.family, self.binding, place, self.context)["status"], "excluded")

    def test_unknown_environment_is_not_good_environment(self):
        """Even any-weather content requires both environmental gates to be known."""
        for field in ("weather_allowed", "air_quality_allowed"):
            for value in (None, "true", 1):
                context = dict(self.context, **{field: value})
                self.assertEqual(assess_conditions(self.family, self.binding, self.place, context)["status"], "needs_context")
            context = dict(self.context, **{field: False})
            self.assertEqual(assess_conditions(self.family, self.binding, self.place, context)["status"], "excluded")

    def test_weather_mismatch_and_sparse_category_do_not_fall_back(self):
        """Do not bypass declared weather needs or invent generic skate/BMX suitability."""
        family = copy.deepcopy(self.family)
        family["weather_tags"] = ["dry"]
        context = dict(self.context, weather_tags=["wet"])
        self.assertEqual(assess_conditions(family, self.binding, self.place, context)["status"], "excluded")
        place = dict(self.place, activity_category="skate_bmx")
        self.assertEqual(assess_conditions(self.family, self.binding, place, self.context)["status"], "excluded")

    def test_preferences_need_binding_and_never_relax_environment(self):
        """Use fixture-only preference codes to test exclusion without inventing production IDs."""
        preferences = {"excluded_codes": ["fixture_explore"]}
        result = assess_conditions(self.family, self.binding, self.place, self.context, preferences)
        self.assertIn("preference_codes_unbound", result["missing"])
        binding = dict(self.binding, preference_codes=["fixture_explore"])
        result = assess_conditions(self.family, binding, self.place, self.context, preferences, "bound")
        self.assertIn("preference_excluded", result["blocked"])
        # Even removing preferences cannot override an adverse air-quality decision.
        context = dict(self.context, air_quality_allowed=False)
        result = assess_conditions(self.family, binding, self.place, context, {}, "bound")
        self.assertIn("air_quality_allowed:false", result["blocked"])

    def test_positive_preferences_are_hints_not_ranking(self):
        """Expose a fixture-only positive match without silently turning it into exclusion."""
        binding = dict(self.binding, preference_codes=["fixture_explore"])
        for codes, expected in ((["fixture_explore"], True), (["fixture_move"], False)):
            result = assess_conditions(self.family, binding, self.place, self.context,
                                       {"preferred_codes": codes}, "bound")
            self.assertEqual(result["status"], "candidate")
            self.assertIs(result["preference_match"], expected)

    def test_malformed_normalized_inputs_do_not_pass(self):
        """Reject malformed preferences and treat null capabilities as missing evidence."""
        place = dict(self.place, confirmed_features=None)
        self.assertEqual(assess_conditions(self.family, self.binding, place, self.context)["status"], "needs_context")
        for preferences in (["fixture"], {"excluded_codes": "fixture"}, {"likes": []}):
            with self.assertRaises(ValueError):
                assess_conditions(self.family, self.binding, self.place, self.context, preferences)
        with self.assertRaises(ValueError):
            assess_conditions(self.family, self.binding, None, self.context)


if __name__ == "__main__":
    unittest.main()
