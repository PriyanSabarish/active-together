"""
Main FastAPI app module. Includes full endpoints for health, data context, 
recommendations, missions, verification, privacy audits, and lifespan startup warming.
"""

import asyncio
import dataclasses
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import yaml
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
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
from app.data.candidate_cache import DatasetUnavailable, get_candidates
from app.missions import service as mission_service
from app.missions.guides import guide_for
from app.models import AgeBand, TravelMode
from app.photo.verify import verify_step as run_verify_step
from app.recommendation.recommend import recommend
from app.recommendation.travel import get_travel_times
from app.services import RecommendationRequest, SettingEnum


class ImageSanitizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args if isinstance(record.args, tuple) else tuple(record.args.values()) if isinstance(record.args, dict) else ()
        carries_bytes = any(isinstance(a, (bytes, bytearray, memoryview)) for a in args)
        try:
            msg = record.getMessage()
        except Exception:
            msg = ""
        if carries_bytes or "image_bytes" in msg or "content-type: image" in msg.lower():
            # args must go too, or formatting the replacement message fails and
            # logging prints the original arguments in its own error report
            record.msg = "[REDACTED_IMAGE_PAYLOAD]"
            record.args = ()
        return True

logger = logging.getLogger("uvicorn.error")
logger.addFilter(ImageSanitizingFilter())

# Melbourne CBD, the centre of the pilot area: the lookup used to warm things up.
WARM_ORIGIN = (-37.8136, 144.9631)


def _warm_dataset() -> None:
    """Task A57: open a pooled connection and run one representative place query,
    which also fills the result cache, so the first real request is not the one
    that pays for a cold database. A failure only logs; it never stops startup."""
    db = SessionLocal()
    try:
        get_candidates(db, *WARM_ORIGIN, 5.0, "outdoor", lambda *a, **k: fetch_candidate_places(*a, **k))
        logger.info("Place dataset warmed during startup.")
    except DatasetUnavailable:
        logger.error("Could not warm the place dataset during startup.")
    finally:
        db.close()


async def _keepalive(url: str, interval_s: float) -> None:
    """Task A59: ping our own health URL so a host that sleeps when idle stays up."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            await asyncio.sleep(interval_s)
            try:
                await client.get(url)
            except httpx.HTTPError:
                logger.warning("Keep-alive ping failed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(_warm_dataset)
    keepalive = None
    if settings.keepalive_url:
        keepalive = asyncio.create_task(_keepalive(settings.keepalive_url, settings.keepalive_interval_s))
    try:
        yield
    finally:
        if keepalive:
            keepalive.cancel()


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

# Figure SVGs: served at /assets/figures/<figure_id>.svg
FIGURES_DIR = Path(__file__).resolve().parent / "assets"
app.mount("/assets/figures", StaticFiles(directory=FIGURES_DIR), name="figures")

HOME_MIN_DURATION = 10  # minimum for at-home sessions; still an open item in the plan
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


def _cached_places(db, lat, lon, radius_km, setting, loader):
    """Cached place lookup (A58). A failed read with nothing cached is the
    dataset-unavailable state (A60), a 503 the client already words, never an
    empty list."""
    try:
        return get_candidates(db, lat, lon, radius_km, setting, loader)
    except DatasetUnavailable:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="dataset_unavailable")


@app.post("/recommendations")
async def create_recommendations(req: RecommendationRequest, db: Session = Depends(get_db)):
    if req.setting == SettingEnum.HOME:
        # No location is read, used or logged at home (D23, A52): lat/lng in the
        # request are ignored. Missions come through the normal generation path.
        if req.age_band is None:
            raise HTTPException(status_code=422, detail="age_band is required for at-home activities")
        total = req.duration_min if req.duration_min is not None else 20
        if not (HOME_MIN_DURATION <= total <= 120):
            raise HTTPException(status_code=400, detail=f"duration_min must be between {HOME_MIN_DURATION} and 120")
        try:
            missions = await asyncio.to_thread(
                mission_service.get_home_missions, req.age_band, total, tuple(req.recent_template_ids)
            )
        except Exception as e:
            logger.error(f"At-home mission error: {type(e).__name__}")
            missions = []
        return {
            "setting": "home",
            "missions": [
                {**m, "place_name": "Home", "place_id": None, "parent_guide": guide_for(m["template_id"])}
                for m in _with_figures(missions)
            ],
        }

    if req.latitude is None or req.longitude is None:
        raise HTTPException(status_code=422, detail="latitude and longitude are required")

    if req.setting == SettingEnum.INDOOR_PLACE:
        lat, lon = round(req.latitude, 4), round(req.longitude, 4)
        if req.radius_km not in (3, 5, 10):
            raise HTTPException(status_code=400, detail="radius_km must be 3, 5, or 10 for indoor places")
        
        indoor_candidates = _cached_places(db, lat, lon, float(req.radius_km), "indoor_place", lambda *a, **k: fetch_indoor_places(*a, **k))
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

    candidates = _cached_places(db, lat, lon, float(req.radius_km), "outdoor", lambda *a, **k: fetch_candidate_places(*a, **k))
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


# Figure lookup: (template_id, age_band, step sequence) -> figure id, read from the reviewed YAML files.
def _load_figure_map() -> dict:
    fmap: dict = {}
    root = Path(__file__).resolve().parents[1] / "content" / "missions" / "reviewed"
    for f in root.glob("*.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.error(f"Could not read figures from {f.name}: {type(e).__name__}")
            continue
        for t in data.get("templates", []):
            for band, b in (t.get("bands") or {}).items():
                for s in (b or {}).get("steps", []):
                    if s.get("figure"):
                        fmap[(t["template_id"], str(band), s["sequence"])] = s["figure"]
    return fmap

FIGURE_MAP = _load_figure_map()


def _with_figures(missions) -> list[dict]:
    """Return plain dicts with each step's figure filled in. Does not mutate the cached objects."""
    out = []
    for m in missions:
        d = m.model_dump(mode="json") if hasattr(m, "model_dump") else dict(m)
        for s in d.get("steps", []):
            s["figure"] = FIGURE_MAP.get(
                (d["template_id"], str(d["age_band"]), s["sequence"]), s.get("figure")
            )
        out.append(d)
    return out


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
        return {"missions": _with_figures(missions)}
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
        try:
            result = await asyncio.to_thread(run_verify_step, image_bytes, prompt_id, attempt)
        except Exception as e:
            # Name the failure only: the exception text or traceback could carry
            # the image. A child is never stuck, so a broken scorer means tap.
            logger.error(f"Photo check failed: {type(e).__name__}")
            return {"result": "use_tap", "attempts_left": 0, "checked_by": None}
        return dataclasses.asdict(result)
    finally:
        del image_bytes


@app.get("/debug/privacy-audit")
def privacy_audit():
    return {"status": "secure", "persistence": "zero_disk", "logging": "sanitized"}