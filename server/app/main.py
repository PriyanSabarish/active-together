from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.data.database import get_db
from app.data.places import fetch_candidate_places
from app.data.weather import fetch_weather_context
from app.models import Context, Place, RecommendationRequest

# from app.recommendation import recommend

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PILOT_LGAS = {"Melbourne", "Monash", "Melton"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/data/places", response_model=list[Place])
def get_places(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = 5.0,
    db: Session = Depends(get_db),
):
    return fetch_candidate_places(db, lat=lat, lon=lon, radius_km=radius_km)


@app.get("/data/context", response_model=Context)
async def get_context(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    return await fetch_weather_context(lat=lat, lon=lon)


@app.post("/recommendations")
async def create_recommendations(
    req: RecommendationRequest,
    db: Session = Depends(get_db),
):
    lat = round(req.latitude, 4)
    lon = round(req.longitude, 4)

    if req.radius_km not in (3, 5, 10):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="radius_km must be 3, 5, or 10")

    if not (20 <= req.duration_min <= 120):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="duration_min must be between 20 and 120")

    try:
        candidates = fetch_candidate_places(db, lat=lat, lon=lon, radius_km=float(req.radius_km))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Places dataset currently unavailable: {e}",
        )

    # A5: Pilot boundary check
    if not candidates or not any(p.lga_name in PILOT_LGAS for p in candidates):
        return {
            "status": "out_of_bounds",
            "message": "Selected location is outside the active pilot area.",
            "combos": [],
        }

    # A6 & A7: Weather context lookup
    context = await fetch_weather_context(lat=lat, lon=lon)

    # A12: Handover to Backend B
    # return recommend(candidates=candidates, context=context, duration_min=req.duration_min)

    return {
        "status": "ok",
        "candidates_found": len(candidates),
        "weather_available": context.available,
        "sample": candidates[:3],
    }