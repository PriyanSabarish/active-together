import httpx
from fastapi.testclient import TestClient

from app import main
from app.data.addresses import _parse_feature, _search_filter


def test_search_filter_is_limited_to_the_three_pilot_lgas():
    result = _search_filter("12 Exhibition Street")
    assert "lga_code IN ('343','344','348')" in result
    assert "house_number_1 = 12" in result
    assert "ezi_address ILIKE '%EXHIBITION%'" in result


def test_search_filter_does_not_allow_cql_injection():
    result = _search_filter("x' OR 1=1")
    assert "1=1" not in result
    assert "x'" not in result.lower()


def test_parse_feature_returns_address_and_epsg4326_coordinates():
    feature = {
        "id": "address.1",
        "geometry": {"type": "Point", "coordinates": [145.12, -37.92]},
        "properties": {
            "pfi": "42",
            "ezi_address": "1 CENTRE ROAD CLAYTON 3168",
            "locality_name": "CLAYTON",
            "postcode": "3168",
            "lga_code": "348",
        },
    }
    assert _parse_feature(feature) == {
        "id": "42",
        "label": "1 Centre Road Clayton VIC 3168",
        "latitude": -37.92,
        "longitude": 145.12,
        "suburb": "Clayton",
        "postcode": "3168",
        "lga_code": "348",
    }


def test_autocomplete_route_returns_suggestions(monkeypatch):
    expected = [{"id": "42", "label": "1 Centre Road Clayton VIC 3168"}]

    async def fake_autocomplete(query, limit):
        assert query == "1 Centre Road"
        assert limit == 5
        return expected

    monkeypatch.setattr(main, "autocomplete_addresses", fake_autocomplete)
    response = TestClient(main.app).get(
        "/locations/autocomplete", params={"q": "1 Centre Road", "limit": 5}
    )

    assert response.status_code == 200
    assert response.json() == {"suggestions": expected}


def test_autocomplete_route_maps_upstream_failure_to_503(monkeypatch):
    async def unavailable(_query, _limit):
        raise httpx.ConnectError("Vicmap unavailable")

    monkeypatch.setattr(main, "autocomplete_addresses", unavailable)
    response = TestClient(main.app).get(
        "/locations/autocomplete", params={"q": "1 Centre Road"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Address search is temporarily unavailable."}