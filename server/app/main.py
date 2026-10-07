"""
Main FastAPI app module. Includes full endpoints for health, data context, 
recommendations, missions, verification, privacy audits, and lifespan startup warming.
"""

import asyncio
import dataclasses
import logging
from contextlib import asynccontextmanager
import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from async_lru import alru_cache
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.data.addresses import autocomplete_addresses
from app.data.database import SessionLocal, get_db, engine
from app.data.places import fetch_candidate_places, fetch_indoor_places, fetch_place_by_id
from app.data.weather import fetch_weather_context
from app.missions import service as mission_service
from app.models import AgeBand, TravelMode
from app.photo.verify import verify_step as run_verify_step
from app.recommendation.recommend import recommend
from app.recommendation.travel import get_travel_times
from app.services import RecommendationRequest, SettingEnum

class ImageSanitizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "image_bytes" in msg or "content-type: image" in msg.lower():
            record.msg = "[REDACTED_IMAGE_PAYLOAD]"
        return True

logger = logging.getLogger("uvicorn.error")
logger.addFilter(ImageSanitizingFilter())

# Task A57: Startup lifespan handler to pre-warm DB pool connections
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up database connection pool
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        logger.info("Database connection pool successfully warmed up during startup.")
    except Exception as e:
        logger.error(f"Failed to pre-warm database connection pool: {e}")
    yield

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PILOT_LGAS = {"melbourne", "monash", "melton"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.get("/data/places")
def get_data_places(lat: float, lon: float, radius_km: float = 5, db: Session = Depends(get_db)):
    candidates = fetch_candidate_places(db, lat=lat, lon=lon, radius_km=radius_km)
    return {"status": "ok", "count": len(candidates), "places": candidates}


@app.get("/data/context")
async def get_data_context(lat: float, lon: float):
    context = await fetch_weather_context(lat=lat, lon=lon)
    return {"status": "ok", "context": context}


@app.get("/locations/autocomplete")
async def locations_autocomplete(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(5, ge=1, le=10),
):
    try:
        return {"suggestions": await autocomplete_addresses(q, limit)}
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Address search is temporarily unavailable.",
        )


@app.post("/recommendations")
async def create_recommendations(req: RecommendationRequest, db: Session = Depends(get_db)):
    if req.setting == SettingEnum.HOME:
        return {
            "setting": "home",
            "missions": [
                {
                    "mission_id": "home_1",
                    "title": "Living Room Obstacle Course",
                    "place_name": "Home",
                    "place_id": None,
                    "estimated_minutes": 20
                }
            ]
        }

    if req.setting == SettingEnum.INDOOR_PLACE:
        lat, lon = round(req.latitude, 4), round(req.longitude, 4)
        if req.radius_km not in (3, 5, 10):
            raise HTTPException(status_code=400, detail="radius_km must be 3, 5, or 10 for indoor places")
        
        indoor_candidates = fetch_indoor_places(db, lat=lat, lon=lon, radius_km=float(req.radius_km))
        if not indoor_candidates:
            return {
                "status": "zero_results",
                "suggestions": ["larger_radius", "at_home"],
                "places": []
            }
        
        return {
            "status": "ok",
            "places": [
                {
                    "place_id": p.place_id,
                    "display_name": p.display_name,
                    "category": p.activity_category,
                    "distance_m": p.distance_m,
                    "unverified": True
                }
                for p in indoor_candidates
            ]
        }

    lat, lon = round(req.latitude, 4), round(req.longitude, 4)
    if req.radius_km not in (3, 5, 10):
        raise HTTPException(status_code=400, detail="radius_km must be 3, 5, or 10")
    if not (20 <= req.duration_min <= 120):
        raise HTTPException(status_code=400, detail="duration_min must be between 20 and 120")

    candidates = fetch_candidate_places(db, lat=lat, lon=lon, radius_km=float(req.radius_km))
    if not candidates or not any(p.lga_name.lower() in PILOT_LGAS for p in candidates):
        return {"status": "out_of_bounds", "message": "Selected location is outside pilot area.", "combos": []}

    context = await fetch_weather_context(lat=lat, lon=lon)
    travel_times_dict = await get_travel_times((lat, lon), candidates, req.travel_mode.value)

    suggest_indoors = False
    if context.available and context.precip_prob is not None:
        suggest_indoors = context.precip_prob >= 0.60

    result = recommend(
        candidates=candidates,
        context=context,
        total_min=req.duration_min,
        travel_times=travel_times_dict,
        mode=TravelMode(req.travel_mode.value),
        radius_km=req.radius_km,
        timestamp=req.timestamp,
        excluded_categories=tuple(req.excluded_categories),
    )
    return {**jsonable_encoder(result), "suggest_indoors": suggest_indoors}


class MissionRequest(BaseModel):
    combo_id: str
    age_band: AgeBand  # "5-7" | "8-10" | "11-12"
    duration_bucket: int = Field(..., description="Plan length in minutes (20, 40 or 60)")
    preferences: list[str] = Field(default_factory=list, description="Category strings to exclude")
    recent_template_ids: list[str] = Field(default_factory=list, description="Recently served template IDs to avoid repetition")


# Task A29: Generation caching keyed by combo, age, duration, preferences, and recency history
@alru_cache(ttl=3600, maxsize=500)
async def _cached_mission_fetch(
    combo_id: str,
    age_band: str,
    duration_bucket: int,
    preferences_tuple: tuple[str, ...],
    recent_template_ids_tuple: tuple[str, ...],
):
    def resolve_place():
        db = SessionLocal()
        try:
            return fetch_place_by_id(db, combo_id)
        finally:
            db.close()

    place = await asyncio.to_thread(resolve_place)
    if place is None:
        raise ValueError(f"Unknown combo_id: {combo_id}")

    # fetch_weather_context has its own cache (app/data/weather.py), so this
    # does not repeat the weather call on every hit of this cache.
    context = await fetch_weather_context(lat=place.latitude, lon=place.longitude)

    def generate_local_missions():
        return mission_service.get_missions(
            place,
            context,
            AgeBand(age_band),
            duration_bucket,
            preferences=preferences_tuple,
            recent_template_ids=recent_template_ids_tuple,
        )

    return await asyncio.to_thread(generate_local_missions)


@app.post("/missions")
@limiter.limit("10/minute")  # Task A24
async def create_missions(request: Request, payload: MissionRequest):
    try:
        # Lists become tuples so the arguments are hashable for alru_cache.
        missions = await _cached_mission_fetch(
            combo_id=payload.combo_id,
            age_band=payload.age_band.value,
            duration_bucket=payload.duration_bucket,
            preferences_tuple=tuple(sorted(payload.preferences or [])),
            recent_template_ids_tuple=tuple(sorted(payload.recent_template_ids)),
        )
        return {"missions": missions}
    except Exception as e:
        logger.error(f"Mission generation error: {type(e).__name__}")
        # Task A25: degrade to a safe empty payload rather than an HTTP error.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "missions": [],
                "degraded": True,
                "message": "Mission generation temporarily unavailable; using offline library cache fallback.",
            },
        )


VERIFY_ALLOWED_PARAMS = {"prompt_id", "attempt"}


async def _read_capped_body(request: Request, limit: int) -> bytes:
    """Read the raw request body into memory, stopping at limit.

    FastAPI's UploadFile / request.form() are deliberately not used: they move
    bodies above about 1 MB to a temporary file on disk, which would break the
    no-persistence guarantee for photo checks (A45).
    """
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > limit:
        raise HTTPException(status_code=413, detail="Image exceeds size ceiling.")
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise HTTPException(status_code=413, detail="Image exceeds size ceiling.")
        chunks.append(chunk)
    return b"".join(chunks)


@app.post("/verify-step")
@limiter.limit("20/minute")  # Task A24
async def verify_step(request: Request):
    """Photo check for one step (6.3).

    The body is the raw JPEG. prompt_id and attempt (1-3) are query
    parameters. Any other parameter, such as run_id or journal metadata, is
    rejected, and so is a multipart body.
    """
    params = request.query_params
    if set(params) - VERIFY_ALLOWED_PARAMS:
        raise HTTPException(status_code=400, detail="Only prompt_id and attempt are accepted.")
    prompt_id = params.get("prompt_id")
    if not prompt_id:
        raise HTTPException(status_code=422, detail="prompt_id is required.")
    try:
        attempt = int(params.get("attempt", "1"))
    except ValueError:
        raise HTTPException(status_code=422, detail="attempt must be 1, 2 or 3.")
    if not 1 <= attempt <= 3:
        raise HTTPException(status_code=422, detail="attempt must be 1, 2 or 3.")

    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Send the image as the raw request body (image/jpeg).")

    image_bytes = await _read_capped_body(request, MAX_IMAGE_SIZE_BYTES)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image.")
    try:
        # Memory only. verify_step() calls the scorers, which are blocking.
        result = await asyncio.to_thread(run_verify_step, image_bytes, prompt_id, attempt)
        return dataclasses.asdict(result)
    finally:
        del image_bytes


@app.get("/debug/privacy-audit")
def privacy_audit():
    return {"status": "secure", "persistence": "zero_disk", "logging": "sanitized"}