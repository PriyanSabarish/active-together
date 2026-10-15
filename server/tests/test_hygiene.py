"""Handover hygiene: logging, debug mode, and no dead modules."""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

import app
from app.config import Settings


def test_every_module_in_the_app_imports():
    """A module that cannot import is dead or broken code (the old routers/ package was both)."""
    failures = []
    for mod in pkgutil.walk_packages(app.__path__, prefix="app."):
        try:
            importlib.import_module(mod.name)
        except Exception as exc:  # noqa: BLE001 - report, do not stop at the first
            failures.append(f"{mod.name}: {type(exc).__name__}: {exc}")
    assert not failures, "\n".join(failures)


def test_the_dead_modules_are_gone():
    root = Path(app.__file__).parent
    assert not (root / "routers").exists()
    assert not (root / "database.py").exists()  # the live one is app/data/database.py


def test_sql_statements_and_their_values_are_not_logged():
    import app.data.database  # noqa: F401 - sets the logger level on import

    level = logging.getLogger("sqlalchemy.engine").getEffectiveLevel()
    assert level >= logging.WARNING


def test_debug_mode_is_off_by_default_and_in_the_shared_env_file():
    assert Settings(_env_file=None).debug is False
    shared = (Path(app.__file__).parent / ".env").read_text(encoding="utf-8")
    assert "DEBUG=false" in shared
