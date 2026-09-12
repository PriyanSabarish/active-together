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
