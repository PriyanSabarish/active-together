"""A57-A60 — place result cache and the dataset-unavailable state."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import settings
from app.data import candidate_cache as cc
from app.data.database import get_db
from tests import fixtures


class Loader:
    def __init__(self, result=("p",), fail=False):
        self.calls, self.result, self.fail = [], list(result), fail

    def __call__(self, db, lat, lon, radius_km):
        self.calls.append((lat, lon, radius_km))
        if self.fail:
            raise RuntimeError("db down")
        return self.result


def test_a_repeat_request_is_served_from_the_cache():
    loader = Loader()
    assert cc.get_candidates(None, -37.8136, 144.9631, 5, "outdoor", loader) == ["p"]
    assert cc.get_candidates(None, -37.8136, 144.9631, 5, "outdoor", loader) == ["p"]
    assert len(loader.calls) == 1


def test_origins_in_the_same_3dp_cell_share_an_entry_and_load_from_the_rounded_origin():
    loader = Loader()
    cc.get_candidates(None, -37.81361, 144.96312, 5, "outdoor", loader)
    cc.get_candidates(None, -37.81364, 144.96308, 5, "outdoor", loader)
    assert loader.calls == [(-37.814, 144.963, 5)]


@pytest.mark.parametrize("a,b", [((5, "outdoor"), (10, "outdoor")), ((5, "outdoor"), (5, "indoor_place"))])
def test_radius_and_setting_are_part_of_the_key(a, b):
    loader = Loader()
    cc.get_candidates(None, -37.8, 144.9, a[0], a[1], loader)
    cc.get_candidates(None, -37.8, 144.9, b[0], b[1], loader)
    assert len(loader.calls) == 2


def test_a_new_dataset_version_drops_cached_results(monkeypatch):
    loader = Loader()
    cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", loader)
    monkeypatch.setattr(settings, "dataset_version", "2")
    cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", loader)
    assert len(loader.calls) == 2


def test_entries_expire(monkeypatch):
    loader = Loader()
    monkeypatch.setattr(settings, "candidate_cache_ttl_s", -1.0)
    cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", loader)
    cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", loader)
    assert len(loader.calls) == 2


def test_a_failed_load_with_nothing_cached_is_unavailable_not_empty():
    with pytest.raises(cc.DatasetUnavailable):
        cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", Loader(fail=True))


def test_a_failure_is_not_cached_so_the_next_request_retries():
    with pytest.raises(cc.DatasetUnavailable):
        cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", Loader(fail=True))
    assert cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", Loader()) == ["p"]


def test_a_genuinely_empty_area_is_cached_as_empty():
    loader = Loader(result=())
    assert cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", loader) == []
    cc.get_candidates(None, -37.8, 144.9, 5, "outdoor", loader)
    assert len(loader.calls) == 1


# endpoint

BODY = {"latitude": -37.81, "longitude": 144.96, "radius_km": 5, "duration_min": 60}


@pytest.fixture
def client():
    main.app.dependency_overrides[get_db] = lambda: None
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_endpoint_returns_503_when_places_cannot_be_read(client, monkeypatch):
    def boom(db, **kw):
        raise RuntimeError("db down")

    monkeypatch.setattr(main, "fetch_candidate_places", boom)
    r = client.post("/recommendations", json=BODY)
    assert r.status_code == 503
    assert r.json()["detail"] == "dataset_unavailable"


def test_indoor_endpoint_returns_503_too_not_an_empty_list(client, monkeypatch):
    def boom(db, **kw):
        raise RuntimeError("no table")

    monkeypatch.setattr(main, "fetch_indoor_places", boom)
    r = client.post("/recommendations", json={**BODY, "setting": "indoor_place"})
    assert r.status_code == 503


def test_the_second_identical_search_does_not_query_again(client, monkeypatch):
    calls = []

    def fake(db, **kw):
        calls.append(kw)
        return list(fixtures.DENSE_INNER)

    async def fake_weather(lat, lon):
        return fixtures.CLEAR_MILD

    async def fake_travel(origin, candidates, mode):
        return {}

    monkeypatch.setattr(main, "fetch_candidate_places", fake)
    monkeypatch.setattr(main, "fetch_weather_context", fake_weather)
    monkeypatch.setattr(main, "get_travel_times", fake_travel)
    client.post("/recommendations", json=BODY)
    client.post("/recommendations", json=BODY)
    assert len(calls) == 1


def test_startup_warm_up_never_raises_when_the_database_is_down(monkeypatch):
    def boom(db, **kw):
        raise RuntimeError("db down")

    class Session:
        def close(self):
            pass

    monkeypatch.setattr(main, "fetch_candidate_places", boom)
    monkeypatch.setattr(main, "SessionLocal", Session)
    main._warm_dataset()  # logs, does not raise
