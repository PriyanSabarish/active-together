"""Daily request budget for an external service, shared by every worker (A41).

The count lives in Postgres (table api_usage) so two gunicorn workers draw on
one budget; an in-process counter would let each spend the full limit. The day
is the Melbourne calendar day, so the budget resets at Melbourne midnight. If
the database cannot be reached the per-process counter is used instead, which
errs towards switching to estimates early rather than overspending.
"""

from __future__ import annotations

import datetime
import logging
from zoneinfo import ZoneInfo

from sqlalchemy import text

logger = logging.getLogger("uvicorn.error")

MELBOURNE = ZoneInfo("Australia/Melbourne")

_CONSUME_SQL = text("""
    INSERT INTO api_usage (day, service, count) VALUES (:day, :service, 1)
    ON CONFLICT (day, service) DO UPDATE SET count = api_usage.count + 1
    RETURNING count
""")

_local = {"day": None, "count": 0}


def _today() -> datetime.date:
    return datetime.datetime.now(MELBOURNE).date()


def try_consume(service: str, limit: int, session_factory=None) -> bool:
    """Spend one request. False when today's budget for this service is used up."""
    day = _today()
    if session_factory is None:
        from app.data.database import SessionLocal as session_factory
    try:
        db = session_factory()
        try:
            count = db.execute(_CONSUME_SQL, {"day": day, "service": service}).scalar_one()
            db.commit()
        finally:
            db.close()
        return count <= limit
    except Exception as exc:
        logger.warning("Shared quota unavailable (%s); using this worker's count", type(exc).__name__)

    if _local["day"] != day:
        _local["day"], _local["count"] = day, 0
    if _local["count"] >= limit:
        return False
    _local["count"] += 1
    return True
