from sqlalchemy import text
from app.database import engine

def recommend(lat: float, lon: float, radius_km: float = 5.0, duration_min: int = 60):
    radius_meters = radius_km * 1000
    
    query = text("""
        SELECT place_id, display_name, activity_category, feature_type, feature_subtype, lga_name,
               ST_Y(location::geometry) AS latitude,
               ST_X(location::geometry) AS longitude,
               ST_Distance(location, ST_GeographyFromText('POINT(' || :lon || ' ' || :lat || ')')) AS distance_meters
        FROM places
        WHERE ST_DWithin(location, ST_GeographyFromText('POINT(' || :lon || ' ' || :lat || ')'), :radius)
        ORDER BY distance_meters ASC
        LIMIT 20;
    """)
    
    try:
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
    except Exception as e:
        print(f"Database query error: {str(e)}")
        raise e