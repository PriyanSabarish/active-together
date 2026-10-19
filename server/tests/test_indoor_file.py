"""The Indoor place list is read from a file shipped with the server, with the database as
the fallback (story 9.3)."""

import csv
import sys
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER / "scripts"))

from app.data import indoor_file, places  # noqa: E402

CARLTON = dict(lat=-37.8001, lon=144.9674)


class ExplodingDb:
    def execute(self, *a, **k):
        raise AssertionError("the database must not be touched when the file is readable")


def test_the_file_serves_indoor_places_without_the_database():
    found = places.fetch_indoor_places(ExplodingDb(), radius_km=3, **CARLTON)
    names = [p.display_name for p in found]
    assert "Carlton Gardens Tennis Club" in names and "Carlton Baths" in names
    assert [p.distance_m for p in found] == sorted(p.distance_m for p in found)  # nearest first
    assert all(p.unverified for p in found)
    assert all(p.distance_m <= 3000 for p in found)


def test_each_name_is_listed_once_and_kinds_come_from_the_name():
    found = places.fetch_indoor_places(ExplodingDb(), radius_km=10, **CARLTON)
    names = [p.display_name for p in found]
    assert len(names) == len(set(names))
    kinds = {p.display_name: p.activity_category for p in found}
    assert kinds["Carlton Baths"] == "swimming"
    assert kinds["Carlton Gardens Tennis Club"] == "clubs"


def test_stadiums_and_unnamed_sites_are_not_in_the_file():
    names = {r.display_name for r in indoor_file.indoor_rows()}
    assert not names & set(places.INDOOR_EXCLUDED_NAMES)
    assert not [n for n in names if n.startswith("Unnamed ")]


def test_nothing_nearby_is_an_empty_list_not_a_database_query():
    assert places.fetch_indoor_places(ExplodingDb(), lat=-35.0, lon=142.0, radius_km=3) == []  # far from any row


def test_an_unusual_radius_snaps_to_an_allowed_one():
    near = places.fetch_indoor_places(ExplodingDb(), radius_km=4, **CARLTON)  # 4 snaps to 3 or 5
    assert all(p.distance_m <= 5000 for p in near)


def test_falls_back_to_the_database_when_the_file_cannot_be_read(monkeypatch):
    def broken(*a, **k):
        raise FileNotFoundError("indoor_places.csv")

    monkeypatch.setattr(indoor_file, "rows_within", broken)
    called = {}

    class Result:
        def mappings(self):
            return self

        def all(self):
            return [dict(place_id="d1", display_name="Carlton Library", activity_category="library", lga_name="MELBOURNE",
                         latitude=-37.8, longitude=144.97, distance_m=500.0, classification_confidence="high")]

    class Db:
        def execute(self, query, params):
            called["yes"] = True
            return Result()

    found = places.fetch_indoor_places(Db(), radius_km=3, **CARLTON)
    assert called and [p.place_id for p in found] == ["d1"]


def test_the_file_is_in_step_with_the_places_data():
    data = SERVER.parent / "data" / "vicmap_app_ready.csv"
    if not data.exists():
        pytest.skip("no data/ folder here")
    import build_indoor_file

    expected = build_indoor_file.build_rows(data)
    with open(indoor_file.INDOOR_FILE_PATH, newline="", encoding="utf-8-sig") as f:
        actual = list(csv.DictReader(f))
    assert actual == expected, "run: python scripts/build_indoor_file.py (from server/) and commit the result"


def test_the_distance_helper_is_close_to_known_values():
    # Melbourne CBD to Carlton Gardens is roughly 1.2 km
    d = indoor_file.distance_m(-37.8136, 144.9631, -37.8029, 144.9715)
    assert 1100 < d < 1500


# nothing inside the radius: the nearest five, however far

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from app.data.candidate_cache import _cache  # noqa: E402
from app.data.database import get_db  # noqa: E402


@pytest.fixture
def api():
    _cache.clear()
    main.app.dependency_overrides[get_db] = lambda: ExplodingDb()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
    _cache.clear()


CLAYTON = {"setting": "indoor_place", "latitude": -37.9150, "longitude": 145.1300, "radius_km": 3}


def test_nothing_in_range_returns_the_nearest_five_and_says_so(api):
    body = api.post("/recommendations", json=CLAYTON).json()
    assert body["status"] == "ok" and body["beyond_radius"] is True
    assert len(body["places"]) == places.NEAREST_COUNT == 5
    dists = [p["distance_m"] for p in body["places"]]
    assert dists == sorted(dists) and dists[0] > 3000  # all beyond the 3 km asked for


def test_something_in_range_is_not_flagged(api):
    body = api.post("/recommendations", json={**CLAYTON, "radius_km": 10}).json()
    assert body["status"] == "ok" and body["beyond_radius"] is False
    assert len(body["places"]) > 5  # the full list, not cut to five


def test_nearest_helper_is_nearest_first_and_capped():
    found = places.fetch_nearest_indoor_places(ExplodingDb(), lat=-37.9150, lon=145.1300)
    assert len(found) == 5 and [p.distance_m for p in found] == sorted(p.distance_m for p in found)
