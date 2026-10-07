"""POST /recommendations returns combos from recommend(), with travel blocks.

The database, weather and routing calls are replaced, so this tests the
endpoint wiring only.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import main
from app.data.database import get_db
from app.models import TravelTime
from tests import fixtures

BODY = {"latitude": -37.81, "longitude": 144.96, "radius_km": 5, "duration_min": 60}


@pytest.fixture
def client(monkeypatch):
    places = tuple(fixtures.DENSE_INNER)

    async def fake_weather(lat, lon):
        return fixtures.CLEAR_MILD

    async def fake_travel(origin, candidates, mode):
        return {p.place_id: TravelTime(minutes=5, source="estimate") for p in candidates}

    monkeypatch.setattr(main, "fetch_candidate_places", lambda db, **kw: places)
    monkeypatch.setattr(main, "fetch_weather_context", fake_weather)
    monkeypatch.setattr(main, "get_travel_times", fake_travel)
    main.app.dependency_overrides[get_db] = lambda: None
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_outdoor_request_returns_combos_with_a_travel_block(client):
    response = client.post("/recommendations", json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["combos"]) == 3
    travel = data["combos"][0]["travel"]
    assert travel["mode"] == "walking"
    assert (travel["out_min"], travel["back_min"]) == (5, 5)
    assert travel["total_min"] == 5 + travel["on_site_min"] + 5
    assert travel["source"] == "estimate"
    assert travel["back_from_outbound"] is True
    assert data["combos"][0]["place"]["place_id"]
    assert data["suggest_indoors"] is False


def test_each_combo_has_its_own_plan_length_field(client):
    data = client.post("/recommendations", json=BODY).json()
    assert all(c["duration_bucket"] == c["travel"]["on_site_min"] for c in data["combos"])


def test_nothing_fits_returns_zero_results_with_suggestions(client):
    data = client.post("/recommendations", json={**BODY, "duration_min": 20}).json()
    assert data["status"] == "zero_results"
    assert data["combos"] == []
    kinds = [s["kind"] for s in data["suggestions"]]
    assert "more_time" in kinds and "other_mode" in kinds
    more = next(s for s in data["suggestions"] if s["kind"] == "more_time")
    assert more["total_min"] == 30 and more["fits_count"] >= 1


def test_travel_mode_is_passed_through(client):
    data = client.post("/recommendations", json={**BODY, "travel_mode": "cycling"}).json()
    assert data["combos"][0]["travel"]["mode"] == "cycling"


def test_suggest_indoors_when_rain_is_60_percent_or_more(client, monkeypatch):
    async def rainy(lat, lon):
        return fixtures.RAIN_AT_THRESHOLD

    monkeypatch.setattr(main, "fetch_weather_context", rainy)
    data = client.post("/recommendations", json=BODY).json()
    assert data["suggest_indoors"] is True
    assert len(data["combos"]) == 3  # results unchanged


def test_weather_unavailable_still_returns_results(client, monkeypatch):
    async def down(lat, lon):
        return fixtures.UNAVAILABLE

    monkeypatch.setattr(main, "fetch_weather_context", down)
    data = client.post("/recommendations", json=BODY).json()
    assert data["suggest_indoors"] is False
    assert len(data["combos"]) == 3


def test_excluded_categories_are_honoured(client):
    data = client.post(
        "/recommendations", json={**BODY, "excluded_categories": ["sports_ground"]}
    ).json()
    assert all(c["place"]["activity_category"] != "sports_ground" for c in data["combos"])
