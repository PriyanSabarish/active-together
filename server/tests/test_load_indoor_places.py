"""Story 9.3 / A53 — the indoor_places schema and the CSV loader's validation."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

spec = importlib.util.spec_from_file_location("load_indoor_places", SCRIPTS / "load_indoor_places.py")
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)

HEADER = "place_id,display_name,activity_category,lga_name,longitude,latitude,source_dataset\n"


def write(tmp_path, body, header=HEADER):
    p = tmp_path / "indoor.csv"
    p.write_text(header + body, encoding="utf-8")
    return p


def test_valid_rows_load_with_optional_columns_empty_as_none(tmp_path):
    rows, rejected = loader.load_rows(write(tmp_path, "i1,Carlton Library,library,MELBOURNE,144.97,-37.80,council\n"))
    assert rejected == []
    assert rows[0]["place_id"] == "i1"
    assert rows[0]["longitude"] == 144.97 and rows[0]["latitude"] == -37.80
    assert rows[0]["source_dataset"] == "council"
    assert rows[0]["feature_type"] is None


def test_unknown_category_is_rejected_not_loaded(tmp_path):
    rows, rejected = loader.load_rows(write(tmp_path, "i1,Some Park,park_and_garden,MELBOURNE,144.97,-37.80,x\n"))
    assert rows == []
    assert "not an indoor category" in rejected[0][1]


@pytest.mark.parametrize("line,reason", [
    (",No Id,library,MELBOURNE,144.97,-37.80,x", "missing place_id"),
    ("i1,,library,MELBOURNE,144.97,-37.80,x", "missing place_id"),
    ("i1,A,library,MELBOURNE,abc,-37.80,x", "not a number"),
    ("i1,A,library,MELBOURNE,144.97,-97.80,x", "out of range"),
])
def test_bad_rows_are_rejected_with_a_reason(tmp_path, line, reason):
    rows, rejected = loader.load_rows(write(tmp_path, line + "\n"))
    assert rows == []
    assert reason in rejected[0][1]


def test_duplicate_place_id_keeps_the_first(tmp_path):
    body = "i1,A,library,MELBOURNE,144.97,-37.80,x\ni1,B,library,MELBOURNE,144.98,-37.81,x\n"
    rows, rejected = loader.load_rows(write(tmp_path, body))
    assert [r["display_name"] for r in rows] == ["A"]
    assert "duplicate" in rejected[0][1]


def test_missing_required_column_raises(tmp_path):
    with pytest.raises(ValueError, match="missing columns"):
        loader.load_rows(write(tmp_path, "i1,A\n", header="place_id,display_name\n"))


def test_schema_defines_indoor_places_with_the_columns_the_query_reads():
    sql = (SCRIPTS / "schema.sql").read_text(encoding="utf-8")
    block = sql[sql.index("CREATE TABLE IF NOT EXISTS indoor_places"):]
    for col in ("place_id", "display_name", "activity_category", "lga_name", "classification_confidence", "location geography(Point, 4326)"):
        assert col in block
    assert "USING GIST (location)" in block


def test_indoor_places_are_given_an_indoor_kind_not_an_outdoor_category():
    from app.data.places import fetch_indoor_places

    class Row(dict):
        pass

    class Result:
        def mappings(self):
            return self
        def all(self):
            return [Row(place_id="i1", display_name="Carlton Library", activity_category="library", lga_name="MELBOURNE",
                        latitude=-37.8, longitude=144.97, distance_m=812.4, classification_confidence="high")]

    class Db:
        def execute(self, *a, **k):
            return Result()

    places = fetch_indoor_places(Db(), lat=-37.8, lon=144.97, radius_km=5)
    assert [p.activity_category for p in places] == ["recreation_centre"]
    assert places[0].unverified is True and places[0].distance_m == 812


def test_indoor_places_are_the_sports_complex_rows_minus_stadiums_and_unnamed_sites():
    from app.data.places import INDOOR_EXCLUDED_NAMES, INDOOR_SUBTYPE, fetch_indoor_places

    seen = {}

    class Result:
        def mappings(self):
            return self

        def all(self):
            return []

    class Db:
        def execute(self, query, params):
            seen["sql"], seen["params"] = str(query), params
            return Result()

    fetch_indoor_places(Db(), lat=-37.8, lon=144.97, radius_km=5)
    assert INDOOR_SUBTYPE == "sports complex"
    assert seen["params"]["subtype"] == "sports complex"
    assert "Mcg" in seen["params"]["excluded"] and "Marvel Stadium" in seen["params"]["excluded"]
    assert set(seen["params"]["excluded"]) == set(INDOOR_EXCLUDED_NAMES)
    assert "FROM places" in seen["sql"] and "feature_subtype = :subtype" in seen["sql"]
    assert "NOT LIKE 'Unnamed %'" in seen["sql"]


def test_the_places_dataset_has_indoor_sports_complexes_in_all_three_councils():
    """Checks the real data file: the rows the query selects exist, stadiums are out, and a
    child-friendly indoor venue is in."""
    import csv
    from pathlib import Path

    from app.data.places import INDOOR_EXCLUDED_NAMES

    path = Path(__file__).resolve().parents[2] / "data" / "vicmap_app_ready.csv"
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["feature_subtype"] == "sports complex"]
    kept = [r for r in rows if r["display_name"] not in INDOOR_EXCLUDED_NAMES and not r["display_name"].startswith("Unnamed ")]
    assert {r["lga_name"] for r in kept} == {"MELBOURNE", "MELTON", "MONASH"}
    names = {r["display_name"] for r in kept}
    assert {"Caroline Springs Leisure Centre", "Swimland Indoor Pool", "Oakleigh Recreation Centre"} <= names
    assert not names & set(INDOOR_EXCLUDED_NAMES)
