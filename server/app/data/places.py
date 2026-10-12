import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
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


# Until real indoor data is loaded into indoor_places (scripts/load_indoor_places.py),
# the Indoor place setting lists these categories from the places table.
# Switch the FROM below to indoor_places and drop the category filter once it is.
INDOOR_STAND_IN_CATEGORIES = ("court", "skate_bmx", "sports_ground")


def fetch_indoor_places(db: Session, lat: float, lon: float, radius_km: float) -> list[IndoorPlace]:
    """
    Fetches indoor places within the specified radius from latitude/longitude,
    limited to INDOOR_STAND_IN_CATEGORIES for now.
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
        WHERE activity_category = ANY(:categories)
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
            {"lat": lat, "lon": lon, "radius_m": radius_km * 1000.0, "categories": list(INDOOR_STAND_IN_CATEGORIES)}
        ).mappings().all()

        return [
            IndoorPlace(
                place_id=r["place_id"],
                display_name=r["display_name"],
                activity_category=r["activity_category"],
                lga_name=r["lga_name"],
                latitude=round(r["latitude"], settings.coordinate_decimal_places),
                longitude=round(r["longitude"], settings.coordinate_decimal_places),
                distance_m=int(round(r["distance_m"])),
                classification_confidence=str(r["classification_confidence"]),
            )
            for r in rows
        ]
    except Exception:
        logging.getLogger("uvicorn.error").exception("Indoor place query failed")
        raise  # a failed read is "dataset unavailable", not "no places nearby"