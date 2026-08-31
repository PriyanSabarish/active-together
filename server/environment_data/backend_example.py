"""Framework-neutral functions that can be wrapped by FastAPI routes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .cache import CacheRepository
from .open_meteo_client import OpenMeteoClient
from .service import EnvironmentService


def create_environment_service(cache_dir: Path) -> EnvironmentService:
    return EnvironmentService(OpenMeteoClient(), CacheRepository(cache_dir))


def get_environment_response(
    service: EnvironmentService, site_name: str, at: str
) -> dict[str, object]:
    """Example endpoint body; `at` must be an ISO-8601 timestamp with offset."""
    requested_at = datetime.fromisoformat(at)
    return service.get_context(site_name, requested_at).to_dict()
