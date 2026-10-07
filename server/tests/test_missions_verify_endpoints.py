"""POST /missions and POST /verify-step wiring (A45, A46/A47 evidence, A51 groundwork).

The database, weather and scorers are replaced, so this tests the endpoint
layer only.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.models import AgeBand
from app.photo.models import Verification
from tests import fixtures

JPEG = b"\xff\xd8\xff\xe0fake-jpeg-bytes"
HEADERS = {"Content-Type": "image/jpeg"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main.limiter, "enabled", False)
    main._cached_mission_fetch.cache_clear()
    yield TestClient(main.app)
    main._cached_mission_fetch.cache_clear()


# /missions


@pytest.fixture
def missions_client(client, monkeypatch):
    place = fixtures.DENSE_INNER[0]

    class FakeSession:
        def close(self):
            pass

    async def fake_weather(lat, lon):
        return fixtures.CLEAR_MILD

    real = main.mission_service.get_missions

    def library_only(*args, **kwargs):
        # never reach the model, whatever GEMINI_API_KEY is in this environment
        return real(*args, **{**kwargs, "model_client": None})

    monkeypatch.setattr(main, "SessionLocal", FakeSession)
    monkeypatch.setattr(main, "fetch_place_by_id", lambda db, pid: place if pid == place.place_id else None)
    monkeypatch.setattr(main, "fetch_weather_context", fake_weather)
    monkeypatch.setattr(main.mission_service, "get_missions", library_only)
    return client, place


def mission_body(place, band="5-7", bucket=20, **extra):
    return {"combo_id": place.place_id, "age_band": band, "duration_bucket": bucket, **extra}


def test_missions_are_served_from_the_reviewed_library(missions_client):
    client, place = missions_client
    data = client.post("/missions", json=mission_body(place)).json()
    assert data.get("degraded") is not True
    assert 1 <= len(data["missions"]) <= 3
    assert all(m["age_band"] == "5-7" for m in data["missions"])


@pytest.mark.parametrize("band", [b.value for b in AgeBand])
@pytest.mark.parametrize("bucket", [20, 40, 60])
def test_every_served_mission_has_a_photo_step_with_a_known_prompt(missions_client, band, bucket):
    from app.photo.vocabulary import load_vocabulary

    known = load_vocabulary()
    client, place = missions_client
    data = client.post("/missions", json=mission_body(place, band, bucket)).json()
    assert data["missions"]
    for mission in data["missions"]:
        photo = [s for s in mission["steps"] if s["verify_mode"] == "photo"]
        assert photo, f"{mission['title']} has no photo step at {bucket} min"
        assert all(s["prompt_id"] in known for s in photo)


def test_unknown_combo_degrades_to_an_empty_payload_not_an_error(missions_client):
    client, place = missions_client
    response = client.post("/missions", json={**mission_body(place), "combo_id": "nope"})
    assert response.status_code == 200
    assert response.json()["missions"] == []
    assert response.json()["degraded"] is True


def test_missions_rejects_a_bad_age_band(missions_client):
    client, place = missions_client
    assert client.post("/missions", json=mission_body(place, band="3-4")).status_code == 422


# /verify-step


@pytest.fixture
def verify_client(client, monkeypatch):
    seen = {}

    def fake(image_bytes, prompt_id, attempt):
        seen.update(size=len(image_bytes), prompt_id=prompt_id, attempt=attempt)
        return Verification("confirmed", 3 - attempt, "api")

    monkeypatch.setattr(main, "run_verify_step", fake)
    client.seen = seen
    return client


def post(client, params="prompt_id=p_red&attempt=1", body=JPEG, headers=HEADERS):
    return client.post(f"/verify-step?{params}", content=body, headers=headers)


def test_verify_returns_the_contract_shape(verify_client):
    response = post(verify_client)
    assert response.status_code == 200
    assert response.json() == {"result": "confirmed", "attempts_left": 2, "checked_by": "api"}
    assert verify_client.seen == {"size": len(JPEG), "prompt_id": "p_red", "attempt": 1}


def test_attempt_defaults_to_one(verify_client):
    assert post(verify_client, "prompt_id=p_red").status_code == 200
    assert verify_client.seen["attempt"] == 1


@pytest.mark.parametrize("params", ["prompt_id=p_red&attempt=1&run_id=abc", "prompt_id=p_red&journal_metadata=x", "prompt_id=p_red&anything=1"])
def test_run_id_and_journal_metadata_are_rejected(verify_client, params):
    assert post(verify_client, params).status_code == 400
    assert verify_client.seen == {}


def test_multipart_upload_is_rejected_so_nothing_can_spool_to_disk(verify_client):
    response = verify_client.post(
        "/verify-step?prompt_id=p_red&attempt=1",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert response.status_code == 400
    assert verify_client.seen == {}


@pytest.mark.parametrize("params", ["attempt=1", "prompt_id=", "prompt_id=p_red&attempt=0", "prompt_id=p_red&attempt=4", "prompt_id=p_red&attempt=x"])
def test_bad_parameters_are_422(verify_client, params):
    assert post(verify_client, params).status_code == 422


def test_empty_body_and_wrong_type_are_400(verify_client):
    assert post(verify_client, body=b"").status_code == 400
    assert post(verify_client, headers={"Content-Type": "text/plain"}).status_code == 400


def test_oversized_image_is_413_before_scoring(verify_client, monkeypatch):
    monkeypatch.setattr(main, "MAX_IMAGE_SIZE_BYTES", 100)
    assert post(verify_client, body=b"x" * 101).status_code == 413
    assert verify_client.seen == {}


def test_large_photo_leaves_nothing_in_temp_directories(verify_client):
    """A body well over the 1 MB spool threshold is handled in memory only."""
    tmp = Path(tempfile.gettempdir())
    before = {p.name for p in tmp.iterdir()}
    big = JPEG + b"\0" * (3 * 1024 * 1024)
    for _ in range(3):
        assert post(verify_client, body=big).status_code == 200
    assert {p.name for p in tmp.iterdir()} - before == set()


def test_failure_responses_do_not_echo_the_image(verify_client):
    secret = b"SECRET-PHOTO-BYTES"
    for response in (post(verify_client, "prompt_id=p_red&run_id=1", body=secret), post(verify_client, "attempt=9", body=secret)):
        assert "SECRET" not in response.text


def test_real_chain_with_nothing_configured_says_tap(client, monkeypatch):
    """No scorer configured and no measured prompts: the child is never stuck."""
    import app.photo.verify as pv

    monkeypatch.setattr(pv, "_default_scorers", [])
    response = post(client)
    assert response.status_code == 200
    assert response.json() == {"result": "use_tap", "attempts_left": 0, "checked_by": None}
