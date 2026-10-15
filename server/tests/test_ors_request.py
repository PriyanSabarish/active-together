"""The OpenRouteService request: profile names, coordinate order, caps and fallbacks."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from app.config import settings
from app.recommendation import travel


class P:
    def __init__(self, i, lat=-37.82, lon=144.97):
        self.place_id, self.latitude, self.longitude = f"p{i}", lat, lon


class FakeResponse:
    def __init__(self, status=200, durations=None):
        self.status_code, self._d = status, durations
        self.request = httpx.Request("POST", "https://x")

    def json(self):
        return {"durations": [self._d]}


class FakeClient:
    calls: list = []
    response = FakeResponse()

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json, headers):
        FakeClient.calls.append((url, json, headers))
        return FakeClient.response


@pytest.fixture(autouse=True)
def ors(monkeypatch):
    FakeClient.calls = []
    FakeClient.response = FakeResponse(durations=[0])
    monkeypatch.setattr(settings, "ors_api_key", "test-key")
    monkeypatch.setattr(travel, "try_consume", lambda *a, **k: True)
    monkeypatch.setattr(travel.httpx, "AsyncClient", FakeClient)


def run(candidates, mode="walking"):
    return asyncio.run(travel.get_travel_times((-37.8136, 144.9631), candidates, mode))


@pytest.mark.parametrize("mode,profile", [("walking", "foot-walking"), ("cycling", "cycling-regular"), ("driving", "driving-car")])
def test_the_request_uses_an_ors_profile_not_our_mode_name(mode, profile):
    FakeClient.response = FakeResponse(durations=[300])
    run([P(1)], mode)
    assert FakeClient.calls[0][0] == f"https://api.openrouteservice.org/v2/matrix/{profile}"


def test_coordinates_go_as_longitude_then_latitude_with_the_origin_rounded_to_3dp():
    FakeClient.response = FakeResponse(durations=[300])
    run([P(1, lat=-37.82, lon=144.97)])
    url, body, headers = FakeClient.calls[0]
    assert body["locations"] == [[144.963, -37.814], [144.97, -37.82]]
    assert body["sources"] == [0] and body["destinations"] == [1]
    assert headers["Authorization"] == "test-key"


def test_seconds_are_rounded_up_to_minutes_and_labelled_routed():
    FakeClient.response = FakeResponse(durations=[301, 600])
    out = run([P(1), P(2)])
    assert out["p1"].minutes == 6 and out["p1"].source == "openrouteservice"
    assert out["p2"].minutes == 10


def test_a_null_duration_gives_that_place_alone_an_estimate():
    FakeClient.response = FakeResponse(durations=[300, None])
    out = run([P(1), P(2)])
    assert out["p1"].source == "openrouteservice"
    assert out["p2"].source == "estimate"


def test_an_error_response_makes_every_time_an_estimate():
    FakeClient.response = FakeResponse(status=404)
    out = run([P(1), P(2)])
    assert {t.source for t in out.values()} == {"estimate"}


def test_only_the_nearest_places_are_sent_and_the_rest_are_estimated():
    n = travel.MAX_ORS_DESTINATIONS + 5
    FakeClient.response = FakeResponse(durations=[120] * travel.MAX_ORS_DESTINATIONS)
    out = run([P(i) for i in range(n)])
    assert len(FakeClient.calls[0][1]["destinations"]) == travel.MAX_ORS_DESTINATIONS
    assert out["p0"].source == "openrouteservice"
    assert out[f"p{n - 1}"].source == "estimate"


def test_a_mode_with_no_profile_is_estimated_without_a_call_or_quota():
    spent = []
    travel.try_consume = lambda *a, **k: spent.append(1) or True
    out = run([P(1)], "teleport")
    assert out["p1"].source == "estimate"
    assert not FakeClient.calls and not spent
