from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Active Together API"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = True

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/active_together"

    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_air_quality_url: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    open_meteo_timeout_seconds: float = 5.0

    allowed_radius_km: tuple[int, ...] = (3, 5, 10)
    min_duration_min: int = 20
    max_duration_min: int = 120
    coordinate_decimal_places: int = 4

    cors_allow_origins: list[str] = ["*"]


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()