"""Indoor place kinds and the parent's preferences for them (story 9.3)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.data.database import get_db
from app.data.indoor_kinds import CLUBS, INDOOR_KINDS, INDOOR_SPORTS, RECREATION, SWIMMING, filter_by_kind, indoor_kind
from app.data.places import INDOOR_EXCLUDED_NAMES, IndoorPlace


@pytest.mark.parametrize("name,kind", [
    ("Swimland Indoor Pool", SWIMMING),
    ("Carlton Baths", SWIMMING),
    ("Monash Aquatic And Recreation Centre", SWIMMING),
    ("Princes Park Carlton Bowls Club", CLUBS),
    ("Royal Park Golf Club", CLUBS),
    ("Cobblebank Indoor Stadium", INDOOR_SPORTS),
    ("State Netball Hockey Centre", INDOOR_SPORTS),
    ("Caroline Springs Leisure Centre", RECREATION),
    ("Kensington Community Centre", RECREATION),
    (None, RECREATION),
])
def test_kind_from_the_name(name, kind):
    assert indoor_kind(name) == kind


def test_a_club_is_a_club_even_when_the_name_mentions_a_pool_or_park():
    assert indoor_kind("Riverside Pool Club") == CLUBS


def test_every_real_indoor_venue_gets_one_of_the_four_kinds_and_each_kind_is_used():
    path = Path(__file__).resolve().parents[2] / "data" / "vicmap_app_ready.csv"
    with open(path, newline="", encoding="utf-8-sig") as f:
        names = [r["display_name"] for r in csv.DictReader(f)
                 if r["feature_subtype"] == "sports complex"
                 and r["display_name"] not in INDOOR_EXCLUDED_NAMES and not r["display_name"].startswith("Unnamed ")]
    kinds = {indoor_kind(n) for n in names}
    assert kinds == set(INDOOR_KINDS)


def place(i, kind):
    return IndoorPlace(place_id=f"i{i}", display_name=f"P{i}", activity_category=kind, lga_name="MELBOURNE",
                       latitude=-37.8, longitude=144.9, distance_m=100 * i)


def test_excluded_kinds_are_dropped():
    places = [place(1, SWIMMING), place(2, CLUBS), place(3, RECREATION)]
    assert [p.place_id for p in filter_by_kind(places, [CLUBS])] == ["i1", "i3"]


def test_excluding_every_kind_keeps_the_list_rather_than_showing_nothing():
    places = [place(1, SWIMMING), place(2, CLUBS)]
    assert filter_by_kind(places, list(INDOOR_KINDS)) == places


def test_no_exclusions_changes_nothing():
    places = [place(1, SWIMMING)]
    assert filter_by_kind(places, []) == places


@pytest.fixture
def client(monkeypatch):
    places = [place(1, SWIMMING), place(2, CLUBS), place(3, RECREATION)]
    monkeypatch.setattr(main, "fetch_indoor_places", lambda db, **kw: places)
    main.app.dependency_overrides[get_db] = lambda: None
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


BODY = {"setting": "indoor_place", "latitude": -37.81, "longitude": 144.96, "radius_km": 5}


def test_endpoint_leaves_out_the_kinds_the_parent_does_not_want(client):
    r = client.post("/recommendations", json={**BODY, "excluded_categories": ["clubs", "swimming"]})
    assert [p["category"] for p in r.json()["places"]] == ["recreation_centre"]


def test_endpoint_without_preferences_returns_everything(client):
    r = client.post("/recommendations", json=BODY)
    assert [p["category"] for p in r.json()["places"]] == ["swimming", "clubs", "recreation_centre"]


# the club places file

def test_club_places_are_the_real_clubs_from_the_team_file():
    from app.data.club_places import club_place_names

    names = club_place_names()
    assert "Royal Park Tennis Club" in names and "Diggers Rest Bowling Club - Lawn Bowls Green" in names
    assert not [n for n in names if "Turf Club" in n]  # walkways, reserve and playground are not clubs
    assert len(names) == 19  # 23 in the file, less the 4 Turf Club places


def test_the_server_copy_matches_data_club_places_csv():
    from app.data.club_places import CLUB_PLACES_PATH

    repo_copy = Path(__file__).resolve().parents[2] / "data" / "club_places.csv"
    if not repo_copy.exists():
        pytest.skip("no data/ folder here")
    assert CLUB_PLACES_PATH.read_bytes() == repo_copy.read_bytes(), "copy data/club_places.csv to server/content/indoor/"


def test_every_club_name_exists_in_the_places_data():
    from app.data.club_places import club_place_names

    path = Path(__file__).resolve().parents[2] / "data" / "vicmap_app_ready.csv"
    with open(path, newline="", encoding="utf-8-sig") as f:
        in_data = {r["display_name"] for r in csv.DictReader(f)}
    assert set(club_place_names()) <= in_data


def test_the_indoor_query_includes_the_clubs_and_lists_each_club_once():
    from app.data.places import fetch_indoor_places_from_db as fetch_indoor_places

    seen = {}

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def mappings(self):
            return self

        def all(self):
            return self.rows

    def row(i, name, d):
        return dict(place_id=f"p{i}", display_name=name, activity_category="court", lga_name="MELBOURNE",
                    latitude=-37.8, longitude=144.9, distance_m=d, classification_confidence="high")

    rows = [row(1, "Royal Park Tennis Club", 100), row(2, "Royal Park Tennis Club", 120), row(3, "Carlton Baths", 300)]

    class Db:
        def execute(self, query, params):
            seen["sql"], seen["params"] = str(query), params
            return Result(rows)

    places = fetch_indoor_places(Db(), lat=-37.8, lon=144.9, radius_km=5)
    assert [p.display_name for p in places] == ["Royal Park Tennis Club", "Carlton Baths"]
    assert [p.place_id for p in places] == ["p1", "p3"]  # the nearest row of the club
    assert "display_name = ANY(:clubs)" in seen["sql"]
    assert "Royal Park Tennis Club" in seen["params"]["clubs"]
