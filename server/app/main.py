from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.data.database import get_db
from app.data.places import fetch_candidate_places
from app.data.weather import fetch_weather_context
from app.models import Context, Place


app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
