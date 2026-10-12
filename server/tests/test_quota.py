"""A41 — one daily OpenRouteService budget shared across workers."""

from __future__ import annotations

import asyncio
import datetime

import pytest

from app.config import settings
from app.data import quota
from app.recommendation import travel


class FakeDb:
    """Stands in for the api_usage table: one shared counter per (day, service)."""

    counts: dict = {}

    def execute(self, sql, params):
        key = (params["day"], params["service"])
        FakeDb.counts[key] = FakeDb.counts.get(key, 0) + 1
        value = FakeDb.counts[key]

        class Result:
            def scalar_one(self):
                return value

        return Result()

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def reset():
    FakeDb.counts = {}
    quota._local.update(day=None, count=0)


def test_two_workers_draw_on_one_budget():
    # every call opens its own session, as two workers would, over the same table
    results = [quota.try_consume("ors", 3, FakeDb) for _ in range(5)]
    assert results == [True, True, True, False, False]


def test_budgets_are_per_service():
    assert quota.try_consume("a", 1, FakeDb)
    assert quota.try_consume("b", 1, FakeDb)
    assert not quota.try_consume("a", 1, FakeDb)


def test_a_new_melbourne_day_resets_the_budget(monkeypatch):
    monkeypatch.setattr(quota, "_today", lambda: datetime.date(2026, 10, 12))
    assert quota.try_consume("ors", 1, FakeDb) and not quota.try_consume("ors", 1, FakeDb)
    monkeypatch.setattr(quota, "_today", lambda: datetime.date(2026, 10, 13))
    assert quota.try_consume("ors", 1, FakeDb)


def test_database_down_falls_back_to_this_workers_count():
    def broken():
        raise RuntimeError("db down")

    assert quota.try_consume("ors", 2, broken) and quota.try_consume("ors", 2, broken)
    assert not quota.try_consume("ors", 2, broken)


def test_schema_creates_the_usage_table():
    from pathlib import Path

    sql = (Path(__file__).resolve().parent.parent / "scripts" / "schema.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS api_usage" in sql
    assert "PRIMARY KEY (day, service)" in sql


class Place:
    def __init__(self, i):
        self.place_id, self.latitude, self.longitude = f"p{i}", -37.82, 144.97


def test_without_a_key_every_time_is_an_estimate_and_no_quota_is_spent(monkeypatch):
    monkeypatch.setattr(settings, "ors_api_key", "")
    spent = []
    monkeypatch.setattr(travel, "try_consume", lambda *a, **k: spent.append(1) or True)
    out = asyncio.run(travel.get_travel_times((-37.81, 144.96), [Place(1)], "walking"))
    assert out["p1"].source == "estimate"
    assert not spent


def test_the_ors_key_is_a_real_setting_read_from_the_environment():
    assert "ors_api_key" in type(settings).model_fields
