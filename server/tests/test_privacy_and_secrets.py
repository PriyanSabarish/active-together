"""A46 scrubbed logging and A49 no committed secrets."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.photo.models import Verification

REPO = Path(__file__).resolve().parents[2]
JPEG = b"\xff\xd8\xff\xe0PRIVATE-PIXELS-" + b"\x00" * 64


def test_log_records_that_mention_image_bytes_are_redacted():
    record = logging.LogRecord("uvicorn.error", logging.ERROR, __file__, 1, "failed with image_bytes=%r", (JPEG,), None)
    assert main.ImageSanitizingFilter().filter(record) is True
    assert "PRIVATE-PIXELS" not in record.getMessage()


def test_a_photo_check_leaves_no_image_data_in_the_logs(monkeypatch, caplog):
    monkeypatch.setattr(main.limiter, "enabled", False)
    monkeypatch.setattr(main, "run_verify_step", lambda image, prompt_id, attempt: Verification("use_tap", 0, None))
    client = TestClient(main.app)
    with caplog.at_level(logging.DEBUG):
        r = client.post("/verify-step?prompt_id=p_red&attempt=1", content=JPEG, headers={"Content-Type": "image/jpeg"})
    assert r.status_code == 200
    assert "PRIVATE-PIXELS" not in caplog.text


def test_a_failing_scorer_means_tap_and_the_image_is_not_in_the_response_or_logs(monkeypatch, caplog):
    monkeypatch.setattr(main.limiter, "enabled", False)

    def boom(image, prompt_id, attempt):
        raise RuntimeError(f"scorer exploded on {image!r}")

    monkeypatch.setattr(main, "run_verify_step", boom)
    client = TestClient(main.app, raise_server_exceptions=False)
    with caplog.at_level(logging.DEBUG):
        r = client.post("/verify-step?prompt_id=p_red&attempt=1", content=JPEG, headers={"Content-Type": "image/jpeg"})
    assert r.status_code == 200
    assert r.json() == {"result": "use_tap", "attempts_left": 0, "checked_by": None}
    assert "PRIVATE-PIXELS" not in r.text + caplog.text


SECRET_PATTERNS = {
    "Google/Gemini API key": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "Groq key": re.compile(r"gsk_[0-9A-Za-z]{20,}"),
    "OpenAI-style key": re.compile(r"sk-[0-9A-Za-z]{32,}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "bearer token literal": re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{30,}"),
}
TEXT_SUFFIXES = {".py", ".js", ".vue", ".json", ".yaml", ".yml", ".md", ".env", ".example", ".txt", ".html", ".toml", ".sql", ".sh"}


def _tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    return [REPO / line for line in out.splitlines() if line]


def test_no_api_key_or_token_is_committed():
    findings = []
    for path in _tracked_files():
        if not path.exists():  # deleted in the working tree, not yet committed
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".env":
            continue
        if "package-lock" in path.name or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(REPO)}: {label}")
    assert not findings, "possible secrets committed:\n" + "\n".join(findings)


def test_real_env_files_are_ignored_by_git():
    ignored = subprocess.run(
        ["git", "check-ignore", "server/.env"], cwd=REPO, capture_output=True, text=True
    )
    assert ignored.returncode == 0, "server/.env must be git-ignored"
