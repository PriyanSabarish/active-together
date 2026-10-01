"""Address autocomplete backed by the Victorian Government Vicmap WFS."""

from __future__ import annotations

import re

import httpx
from async_lru import alru_cache

VICMAP_WFS_URL = "https://opendata.maps.vic.gov.au/geoserver/wfs"
PILOT_LGA_CODES = ("343", "344", "348")  # Melbourne, Melton, Monash
MAX_QUERY_LENGTH = 100


def _escape_cql(value: str) -> str:
    return value.replace("'", "''")


def _search_filter(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9-]+", query.upper())[:8]
    address_clauses = []
    for token in tokens:
        if token.isdigit():
            number = int(token)
            address_clauses.append(
                f"(house_number_1 = {number} OR disp_number_1 = {number})"
            )
        else:
            address_clauses.append(f"ezi_address ILIKE '%{_escape_cql(token)}%'")
    lgas = ",".join(f"'{code}'" for code in PILOT_LGA_CODES)
    return (
        f"lga_code IN ({lgas}) AND property_status = 'A' "
        f"AND is_primary = 'Y' AND " + " AND ".join(address_clauses)
    )


def _parse_feature(feature: dict) -> dict | None:
    properties = feature.get("properties") or {}
    coordinates = (feature.get("geometry") or {}).get("coordinates") or []
    if len(coordinates) < 2 or not properties.get("ezi_address"):
        return None
    try:
        longitude, latitude = float(coordinates[0]), float(coordinates[1])
    except (TypeError, ValueError):
        return None
    postcode = str(properties.get("postcode") or "")
    label = str(properties["ezi_address"]).title()
    if postcode and label.endswith(postcode):
        label = f"{label[:-len(postcode)].rstrip()} VIC {postcode}"
    return {
        "id": str(properties.get("pfi") or feature.get("id") or ""),
        "label": label,
        "latitude": latitude,
        "longitude": longitude,
        "suburb": str(properties.get("locality_name") or "").title(),
        "postcode": postcode,
        "lga_code": str(properties.get("lga_code") or ""),
    }


@alru_cache(maxsize=256, ttl=300)
async def autocomplete_addresses(query: str, limit: int = 5) -> list[dict]:
    query = " ".join(query.strip().split())[:MAX_QUERY_LENGTH]
    if len(query) < 3 or not re.search(r"[A-Za-z0-9]", query):
        return []

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "open-data-platform:address",
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "count": str(min(max(limit * 4, 10), 40)),
        "propertyName": "pfi,ezi_address,locality_name,lga_code,postcode,geom",
        "cql_filter": _search_filter(query),
    }
    timeout = httpx.Timeout(8.0, connect=4.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(VICMAP_WFS_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    seen: set[str] = set()
    suggestions: list[dict] = []
    for feature in payload.get("features", []):
        suggestion = _parse_feature(feature)
        if suggestion and suggestion["label"] not in seen:
            seen.add(suggestion["label"])
            suggestions.append(suggestion)
            if len(suggestions) >= limit:
                break
    return suggestions
