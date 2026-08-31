"""Validated, atomic local storage for seven-day environment forecasts."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import EnvironmentContext


SCHEMA_VERSION = 1


class CacheError(RuntimeError):
    pass


class ForecastNotCached(CacheError):
    pass


def floor_hour(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Requested time must include a timezone")
    return value.astimezone(UTC).replace(minute=0, second=0, microsecond=0)


def _records_checksum(records: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class CacheRepository:
    def __init__(self, directory: Path):
        self.directory = directory
        self.offline_path = directory / "environment-bundle-v1.json.gz"
        self.live_path = directory / "latest-live-forecast-v1.json.gz"

    def _write(self, path: Path, contexts: list[EnvironmentContext], kind: str) -> None:
        if not contexts:
            raise CacheError("Cannot write an empty forecast cache")
        records = [item.to_dict() for item in sorted(
            contexts, key=lambda row: (row.site_name, row.timestamp_utc)
        )]
        keys = [(row["site_name"], row["timestamp_utc"]) for row in records]
        if len(keys) != len(set(keys)):
            raise CacheError("Duplicate site-time keys cannot be cached")
        payload = {
            "manifest": {
                "schema_version": SCHEMA_VERSION,
                "kind": kind,
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "forecast_start_utc": min(row["timestamp_utc"] for row in records),
                "forecast_end_utc": max(row["timestamp_utc"] for row in records),
                "location_count": len({row["site_name"] for row in records}),
                "record_count": len(records),
                "provider": "Open-Meteo",
                "forecast_days_requested": 7,
                "records_sha256": _records_checksum(records),
            },
            "records": records,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with gzip.open(temporary, "wt", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        temporary.replace(path)

    def write_offline_bundle(self, contexts: list[EnvironmentContext]) -> None:
        sites = {item.site_name for item in contexts}
        if sites != {"melton", "melbourne", "monash"}:
            raise CacheError(f"Offline bundle must contain all three pilot sites: {sites}")
        timestamps_by_site = {
            site: {item.timestamp_utc for item in contexts if item.site_name == site}
            for site in sites
        }
        counts = {site: len(values) for site, values in timestamps_by_site.items()}
        if counts != {"melton": 168, "melbourne": 168, "monash": 168}:
            raise CacheError(
                f"A seven-day hourly bundle requires 168 records per site; found {counts}"
            )
        time_axes = list(timestamps_by_site.values())
        if any(axis != time_axes[0] for axis in time_axes[1:]):
            raise CacheError("All three pilot sites must use the same hourly time axis")
        self._write(self.offline_path, contexts, "offline_bundle")

    def write_live_forecast(self, contexts: list[EnvironmentContext]) -> None:
        incoming_sites = {item.site_name for item in contexts}
        retained: list[EnvironmentContext] = []
        if self.live_path.exists():
            try:
                retained = [
                    item for item in self.read(self.live_path)
                    if item.site_name not in incoming_sites
                ]
            except CacheError:
                retained = []
        self._write(self.live_path, retained + contexts, "live_fallback")

    def read(self, path: Path) -> list[EnvironmentContext]:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
            raise CacheError(f"Cannot read cache {path}: {exc}") from exc
        manifest = payload.get("manifest", {})
        records = payload.get("records")
        if manifest.get("schema_version") != SCHEMA_VERSION or not isinstance(records, list):
            raise CacheError("Unsupported or malformed cache schema")
        if manifest.get("record_count") != len(records):
            raise CacheError("Cache record count does not match manifest")
        if manifest.get("records_sha256") != _records_checksum(records):
            raise CacheError("Cache checksum validation failed")
        contexts = [EnvironmentContext.from_dict(item) for item in records]
        keys = [(item.site_name, item.timestamp_utc) for item in contexts]
        if len(keys) != len(set(keys)):
            raise CacheError("Cache contains duplicate site-time keys")
        return contexts

    def find(self, site_name: str, requested_at: datetime) -> EnvironmentContext:
        target = floor_hour(requested_at)
        candidates: list[EnvironmentContext] = []
        for path in (self.live_path, self.offline_path):
            if not path.exists():
                continue
            try:
                match = next(
                    item for item in self.read(path)
                    if item.site_name == site_name and item.timestamp_utc == target
                )
            except (CacheError, StopIteration):
                continue
            candidates.append(match)
        if not candidates:
            raise ForecastNotCached(
                f"No cached forecast for {site_name} at {target.isoformat()}"
            )
        newest = max(candidates, key=lambda item: item.fetched_at_utc)
        return replace(newest, source_mode="cached")

    def status(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for label, path in (("live", self.live_path), ("offline", self.offline_path)):
            if not path.exists():
                result[label] = {"available": False}
                continue
            try:
                records = self.read(path)
                result[label] = {
                    "available": True,
                    "record_count": len(records),
                    "sites": sorted({item.site_name for item in records}),
                    "forecast_start_utc": min(item.timestamp_utc for item in records).isoformat(),
                    "forecast_end_utc": max(item.timestamp_utc for item in records).isoformat(),
                    "fetched_at_utc": max(item.fetched_at_utc for item in records).isoformat(),
                }
            except CacheError as exc:
                result[label] = {"available": False, "error": str(exc)}
        return result
