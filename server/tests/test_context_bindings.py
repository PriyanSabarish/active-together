from __future__ import annotations

from app.missions.context_bindings import load_eligible_categories


def test_loads_the_real_bindings_file():
    bindings = load_eligible_categories()
    assert len(bindings) == 18


def test_colour_hunt_eligible_categories_match_the_real_file():
    bindings = load_eligible_categories()
    assert bindings["activity_colour_hunt"] == ["park_and_garden", "picnic_day_use", "playground", "trail_access"]


def test_missing_template_id_is_not_present():
    bindings = load_eligible_categories()
    assert "not_a_real_template" not in bindings


def test_custom_path_and_missing_eligible_categories_key(tmp_path):
    path = tmp_path / "bindings.yaml"
    path.write_text(
        "templates:\n"
        "  - template_id: fx_no_categories\n"
        "    eligible_place_categories: []\n"
        "  - template_id: fx_with_categories\n"
        "    eligible_place_categories: [playground, court]\n",
        encoding="utf-8",
    )

    bindings = load_eligible_categories(path)
    assert bindings == {"fx_no_categories": [], "fx_with_categories": ["playground", "court"]}
