import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.data.club_places import club_place_names
from app.data import indoor_file
from app.data.indoor_kinds import indoor_kind
from app.models import ActivityCategory, Place

PLACE_BY_ID_QUERY = text("""
    SELECT
    place_id,
    display_name,
    activity_category,
    lga_name,
    ST_Y(location::geometry) AS latitude,
    ST_X(location::geometry) AS longitude,
    classification_confidence
   FROM places
WHERE place_id = :place_id;
""")

PLACES_QUERY = text("""
    SELECT
    place_id,
    display_name,
    activity_category,
    lga_name,
    ST_Y(location::geometry) AS latitude,
    ST_X(location::geometry) AS longitude,
    ST_Distance(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_m,
    classification_confidence
   FROM places
WHERE ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
    :radius_m
)
ORDER BY distance_m ASC;
""")


def fetch_candidate_places(db: Session, lat: float, lon: float, radius_km: float) -> list[Place]:
    if radius_km not in settings.allowed_radius_km:
        radius_km = min(settings.allowed_radius_km, key=lambda r: abs(r - radius_km))

    rows = db.execute(
        PLACES_QUERY,
        {"lat": lat, "lon": lon, "radius_m": radius_km * 1000.0}
    ).mappings().all()

    return [
        Place(
            place_id=r["place_id"],
            display_name=r["display_name"],
            activity_category=ActivityCategory(r["activity_category"]),
            lga_name=r["lga_name"],
            latitude=round(r["latitude"], settings.coordinate_decimal_places),
            longitude=round(r["longitude"], settings.coordinate_decimal_places),
            distance_m=int(round(r["distance_m"])),
            classification_confidence=str(r["classification_confidence"]),
        )
        for r in rows
    ]


def fetch_place_by_id(db: Session, place_id: str) -> Place | None:
    """Resolves a combo_id (== place_id, see app.recommendation.recommend)
    back to a Place for /missions — stateless, so it works the same
    regardless of which gunicorn worker or instance handles the request,
    unlike an in-memory combo cache would.

    distance_m has no meaning without a search origin here; 0 is a
    placeholder — nothing in mission generation reads it.
    """
    row = db.execute(PLACE_BY_ID_QUERY, {"place_id": place_id}).mappings().first()
    if row is None:
        return None

    return Place(
        place_id=row["place_id"],
        display_name=row["display_name"],
        activity_category=ActivityCategory(row["activity_category"]),
        lga_name=row["lga_name"],
        latitude=round(row["latitude"], settings.coordinate_decimal_places),
        longitude=round(row["longitude"], settings.coordinate_decimal_places),
        distance_m=0,
        classification_confidence=str(row["classification_confidence"]),
    )

@dataclass(frozen=True)
class IndoorPlace:
    """An indoor place (story 9.3). Not app.models.Place: its category is an
    indoor one, not an ActivityCategory, and it is always unverified (D25)."""
    place_id: str
    display_name: str | None
    activity_category: str
    lga_name: str
    latitude: float
    longitude: float
    distance_m: int
    classification_confidence: str | None = None
    unverified: bool = True


# Until real indoor data is loaded into indoor_places (scripts/load_indoor_places.py), the
# Indoor place setting lists the "sports complex" rows of the places table: leisure
# centres, baths, aquatic centres and indoor stadiums (data/vicmap_app_ready.csv), plus the club
# places in data/club_places.csv (see app/data/club_places.py).
# Switch the FROM below to indoor_places and drop these filters once that table is loaded.
INDOOR_SUBTYPE = "sports complex"
# Stadiums and arenas are not somewhere to take a child to play, so they are left out.
INDOOR_EXCLUDED_NAMES = (
    "Mcg", "Marvel Stadium", "Rod Laver Arena", "Margaret Court Arena", "John Cain Arena",
    "Ikon Park", "Aami Park", "Melbourne Park", "Olympic Park", "Olympic Park Oval", "Festival Hall",
)


def _snap_radius(radius_km: float) -> float:
    if radius_km not in settings.allowed_radius_km:
        return min(settings.allowed_radius_km, key=lambda r: abs(r - radius_km))
    return radius_km


def fetch_indoor_places(db: Session, lat: float, lon: float, radius_km: float | None) -> list[IndoorPlace]:
    """
    Indoor places near a point. Reads the indoor file shipped with the server first (no
    database needed); only if that file cannot be read does it query the places table.
    An empty result from a readable file is a real "nothing nearby", not a failure.
    A radius of None lists every indoor place, nearest first (the caller takes the first few).
    """
    radius_km = None if radius_km is None else _snap_radius(radius_km)
    try:
        found = indoor_file.rows_within(lat, lon, radius_km)
    except Exception:
        logging.getLogger("uvicorn.error").exception("Indoor places file unavailable, using the database")
        return fetch_indoor_places_from_db(db, lat, lon, radius_km if radius_km is not None else max(settings.allowed_radius_km))

    places, seen = [], set()
    for row, d in found:  # nearest first, so the first row of a name is its nearest
        if row.display_name in seen:
            continue
        seen.add(row.display_name)
        places.append(
            IndoorPlace(
                place_id=row.place_id,
                display_name=row.display_name,
                activity_category=indoor_kind(row.display_name),
                lga_name=row.lga_name,
                latitude=round(row.latitude, settings.coordinate_decimal_places),
                longitude=round(row.longitude, settings.coordinate_decimal_places),
                distance_m=int(round(d)),
                classification_confidence=row.classification_confidence,
            )
        )
    return places


NEAREST_COUNT = 5


def fetch_nearest_indoor_places(db: Session, lat: float, lon: float) -> list[IndoorPlace]:
    """The nearest few indoor places however far away, for when none is inside the search radius."""
    return fetch_indoor_places(db, lat, lon, None)[:NEAREST_COUNT]


def fetch_indoor_places_from_db(db: Session, lat: float, lon: float, radius_km: float) -> list[IndoorPlace]:
    """
    Fetches indoor places within the specified radius from latitude/longitude,
    limited to the sports complex rows for now (see INDOOR_SUBTYPE), minus stadiums and
    unnamed sites, plus the club places. A club with several rows (one per court) is
    listed once, at its nearest row.
    Orders results by distance ascending, then display name.
    """
    indoor_query = text("""
        SELECT
            place_id,
            display_name,
            activity_category,
            lga_name,
            ST_Y(location::geometry) AS latitude,
            ST_X(location::geometry) AS longitude,
            ST_Distance(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_m,
            classification_confidence
        FROM places
        WHERE (
            (feature_subtype = :subtype AND display_name <> ALL(:excluded) AND display_name NOT LIKE 'Unnamed %')
            OR display_name = ANY(:clubs)
          )
          AND ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radius_m
        )
        ORDER BY distance_m ASC, display_name ASC;
    """)

    if radius_km not in settings.allowed_radius_km:
        radius_km = min(settings.allowed_radius_km, key=lambda r: abs(r - radius_km))

    try:
        rows = db.execute(
            indoor_query,
            {"lat": lat, "lon": lon, "radius_m": radius_km * 1000.0, "subtype": INDOOR_SUBTYPE, "excluded": list(INDOOR_EXCLUDED_NAMES), "clubs": list(club_place_names())}
        ).mappings().all()

        places, seen = [], set()
        for r in rows:  # nearest first, so the first row of a name is its nearest
            if r["display_name"] in seen:
                continue
            seen.add(r["display_name"])
            places.append(
                IndoorPlace(
                    place_id=r["place_id"],
                    display_name=r["display_name"],
                    activity_category=indoor_kind(r["display_name"]),
                    lga_name=r["lga_name"],
                    latitude=round(r["latitude"], settings.coordinate_decimal_places),
                    longitude=round(r["longitude"], settings.coordinate_decimal_places),
                    distance_m=int(round(r["distance_m"])),
                    classification_confidence=str(r["classification_confidence"]),
                )
            )
        return places
    except Exception:
        logging.getLogger("uvicorn.error").exception("Indoor place query failed")
        raise  # a failed read is "dataset unavailable", not "no places nearby"