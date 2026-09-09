from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Active Together API"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = True

    database_url: str = "postgresql+pg8000://postgres:postgres@localhost:5433/active_together"

    # legacy Open-Meteo config — no longer used by weather.py, safe to remove once confirmed unused elsewhere
    open_meteo_timeout_seconds: float = 5.0

    # WeatherAPI.com — required, no default, coming from env var WEATHERAPI_KEY
    weatherapi_key: str
    weatherapi_url: str = "https://api.weatherapi.com/v1/forecast.json"

    allowed_radius_km: tuple[int, ...] = (3, 5, 10)
    min_duration_min: int = 20
    max_duration_min: int = 120
    coordinate_decimal_places: int = 4

    cors_allow_origins: list[str] = ["*"]


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()