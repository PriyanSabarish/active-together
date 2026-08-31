from fastapi import APIRouter
from app.models import RecommendationRequest
from app.services import recommend

router = APIRouter()

@router.post("/recommendations")
def get_recommendations(payload: RecommendationRequest):
    return recommend(
        lat=payload.latitude,
        lon=payload.longitude,
        radius_km=payload.radius_km,
        duration_min=payload.duration_min
    )