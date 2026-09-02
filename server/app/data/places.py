from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ActivityCategory, Place

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