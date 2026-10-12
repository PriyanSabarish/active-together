"""Story 9.2 — POST /recommendations with setting "home".

No database, weather or routing is involved: an at-home request must not touch
any of them, and must not use the location it was sent.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import main
from app.data.database import get_db
from app.missions import service
from app.models import AgeBand

HOME = {"setting": "home", "duration_min": 40, "age_band": "8-10"}


@pytest.fixture
def client(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("an at-home request must not read places, weather or travel times")

    async def forbidden_async(*a, **k):
        forbidden()

    monkeypatch.setattr(main, "fetch_candidate_places", forbidden)
    monkeypatch.setattr(main, "fetch_indoor_places", forbidden)
    monkeypatch.setattr(main, "fetch_weather_context", forbidden_async)
    monkeypatch.setattr(main, "get_travel_times", forbidden_async)
    main.app.dependency_overrides[get_db] = lambda: None
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_home_returns_two_or_three_missions_for_home(client):
    r = client.post("/recommendations", json=HOME)
    assert r.status_code == 200
    body = r.json()
    assert body["setting"] == "home"
    assert 2 <= len(body["missions"]) <= 3
    for m in body["missions"]:
        assert m["place_name"] == "Home" and m["place_id"] is None
        assert m["template_id"].startswith("activity_home_")
        assert m["age_band"] == "8-10"
        assert len(m["steps"]) == 5


def test_location_sent_with_a_home_request_is_ignored(client):
    with_loc = client.post("/recommendations", json={**HOME, "latitude": -37.81, "longitude": 144.96})
    without = client.post("/recommendations", json=HOME)
    assert with_loc.status_code == 200
    strip = lambda body: [{k: v for k, v in m.items() if k != "mission_id"} for m in body["missions"]]
    assert strip(with_loc.json()) == strip(without.json())


def test_a_short_session_gets_the_20_minute_plan(client):
    r = client.post("/recommendations", json={**HOME, "duration_min": 15})
    assert r.status_code == 200
    assert {len(m["steps"]) for m in r.json()["missions"]} == {3}


def test_age_band_is_required(client):
    r = client.post("/recommendations", json={"setting": "home", "duration_min": 40})
    assert r.status_code == 422


@pytest.mark.parametrize("minutes", [5, 121])
def test_duration_out_of_range_is_rejected(client, minutes):
    assert client.post("/recommendations", json={**HOME, "duration_min": minutes}).status_code == 400


def test_recently_played_templates_are_deprioritised(client):
    first = client.post("/recommendations", json=HOME).json()["missions"]
    recent = [first[0]["template_id"]]
    again = client.post("/recommendations", json={**HOME, "recent_template_ids": recent}).json()["missions"]
    assert again[0]["template_id"] != recent[0]


def test_outdoor_without_coordinates_is_rejected(client):
    assert client.post("/recommendations", json={"duration_min": 60}).status_code == 422
    assert client.post("/recommendations", json={"setting": "indoor_place", "radius_km": 5}).status_code == 422


def test_home_missions_are_checked_by_the_home_safety_rules(monkeypatch):
    seen = []
    real = service.generate_missions

    def spy(*a, **k):
        seen.append(k.get("setting"))
        return real(*a, **k)

    monkeypatch.setattr(service, "generate_missions", spy)
    assert service.get_home_missions(AgeBand.BAND_8_10, 40)
    assert seen and all(str(s.value if hasattr(s, "value") else s) == "home" for s in seen)
