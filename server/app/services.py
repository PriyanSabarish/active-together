from sqlalchemy import text
from app.database import engine

def recommend(lat: float, lon: float, radius_km: float = 5.0, duration_min: int = 60):
    # Convert kilometers to meters for PostGIS spatial queries
    radius_meters = radius_km * 1000
    
    query = text("""
        SELECT place_id, display_name, activity_category, feature_type, feature_subtype, lga_name,
               ST_Y(location::geometry) as latitude,
               ST_X(location::geometry) as longitude,
               ST_Distance(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS distance_meters
        FROM places
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
        ORDER BY distance_meters ASC
        LIMIT 20;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"lat": lat, "lon": lon, "radius": radius_meters})
        places = [dict(row) for row in result.mappings().all()]
        
    return {
        "search_parameters": {
            "latitude": lat,
            "longitude": lon,
            "radius_km": radius_km,
            "duration_min": duration_min
        },
        "total_matches": len(places),
        "combos": places
    }