"""
Preference filter (B28) — ahead of ranking, with the relaxation rule when
strict filtering would return zero results.

Runs on eligible Place candidates before order_candidates ranks them.
Excluding every place in an excluded category is fine when something is
left; when it would leave nothing, the filter relaxes back to the
unfiltered set rather than the request coming back zero-result purely
because of a preference exclusion (story 4.3).
"""

from __future__ import annotations

from typing import Iterable

from app.models import ActivityCategory, Place


def filter_by_preference(
    places: tuple[Place, ...],
    excluded_categories: Iterable[ActivityCategory] = (),
) -> tuple[Place, ...]:
    excluded = frozenset(excluded_categories)
    if not excluded:
        return places

    filtered = tuple(p for p in places if p.activity_category not in excluded)

    return filtered if filtered else places
