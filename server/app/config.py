from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # server/app/.env is tracked in git and holds shared, non-secret defaults.
        # server/.env is git-ignored, for secrets and personal overrides (a
        # different local database port, say). Later files win, so it wins.
        env_file=(Path(__file__).with_name(".env"), Path(__file__).parent.parent / ".env"),
        extra="ignore",
    )

    app_name: str = "Active Together API"
    environment: Literal["local", "staging", "production"] = "local"
    # False unless asked for: debug mode puts tracebacks (and so exception text) in error
    # responses. Set DEBUG=true in server/.env (git-ignored) for local development.
    debug: bool = False

    database_url: str = "postgresql+pg8000://postgres:postgres@localhost:5433/active_together"

    # legacy Open-Meteo config — no longer used by weather.py, safe to remove once confirmed unused elsewhere
    open_meteo_timeout_seconds: float = 5.0

    # WeatherAPI.com — required, no default, coming from env var WEATHERAPI_KEY
    # Optional for local development; weather.py degrades to unavailable when
    # the key is absent, while places and address search continue to work.
    weatherapi_key: str = ""
    weatherapi_url: str = "https://api.weatherapi.com/v1/forecast.json"

    # Gemini API (B37) — optional so the app boots and tests run with no key
    # at all; only GeminiModelClient needs it, and only once something
    # actually wires it up. A18b: lives in an environment variable only,
    # never in the repository.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"

    # Photo checks (iteration 3, B52/B53/B55). All optional so the app boots and
    # tests run with nothing configured; with nothing set every photo step
    # falls back to a tap. photo_api_enabled stays False until the mentor has
    # signed off on sending photos to the Gemini API (D6) and the data terms
    # are confirmed (D2). Host URL and token live in environment variables only.
    photo_api_enabled: bool = False
    # True (default): a scorer is only asked about prompts measured and kept
    # for it (B54). False: candidate prompts are asked too, so photo checks
    # work before any measurement exists. Prompts marked dropped are never
    # asked either way. The accuracy of unmeasured checks is not known.
    photo_require_measured: bool = True
    inference_host_url: str | None = None
    inference_host_token: str | None = None
    photo_check_timeout_s: float = 8.0
    # Thinking level for photo-check calls; empty string sends none. Some models
    # reject the field, in which case set PHOTO_GEMINI_THINKING_LEVEL= (empty).
    photo_gemini_thinking_level: str = "minimal"
    # Same idea for mission-text generation. Without it the model "thinks" for
    # seconds and the 5 s generation budget runs out. Empty string sends none.
    gemini_thinking_level: str = "minimal"
    # False: serve the reviewed library wording as written and never call Gemini
    # for mission text (instant, and no model rewrite of the steps). Photo
    # checks are unaffected. Set MISSION_GENERATION_ENABLED=false for the demo.
    mission_generation_enabled: bool = True

    # OpenRouteService (A37). Empty: every travel time is a labelled estimate.
    # Lives in an environment variable only, never in the repository.
    ors_api_key: str = ""
    ors_daily_limit: int = 400  # academic quota safeguard (A41)

    # Place lookups (A57-A60). Bump DATASET_VERSION after a pipeline refresh so
    # cached results are dropped. KEEPALIVE_URL, when set, is pinged so a host
    # that sleeps when idle stays awake.
    dataset_version: str = "1"
    candidate_cache_ttl_s: float = 3600.0
    keepalive_url: str | None = None
    keepalive_interval_s: float = 600.0

    # Travel spread (iteration 3): "spread" picks the top three across the
    # travel range and across activity kinds; "nearest" is the old nearest-3.
    travel_spread_band_count: int = 3
    travel_spread_min_band_width_min: int = 5
    travel_spread_default_mode: Literal["spread", "nearest"] = "spread"

    allowed_radius_km: tuple[int, ...] = (3, 5, 10)
    min_duration_min: int = 20
    max_duration_min: int = 120
    coordinate_decimal_places: int = 4

    cors_allow_origins: list[str] = ["*"]


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
