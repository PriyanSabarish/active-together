"""Test isolation: a developer's real server/.env (Gemini key, photo flags) must not change test outcomes."""

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _default_photo_settings(monkeypatch):
    monkeypatch.setattr(settings, "photo_require_measured", True)
    monkeypatch.setattr(settings, "photo_api_enabled", False)
    monkeypatch.setattr(settings, "inference_host_url", None)
    monkeypatch.setattr(settings, "inference_host_token", None)
