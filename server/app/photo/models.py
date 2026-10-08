"""Shared types for photo checks (iteration 3, section 5.3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Result = Literal["confirmed", "retry", "use_tap"]
CheckedBy = Literal["own_host", "api"]

MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class Verification:
    """What verify_step() returns, field for field the /verify-step response."""

    result: Result
    attempts_left: int
    checked_by: CheckedBy | None


@dataclass(frozen=True)
class ScorerStatus:
    """One scorer's measured standing on one prompt, written by B54."""

    status: str = "candidate"  # candidate | kept | dropped
    threshold: float | None = None  # own_host only: minimum similarity to confirm
    accuracy: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None


@dataclass(frozen=True)
class Prompt:
    id: str
    text: str
    scorers: dict[str, ScorerStatus] = field(default_factory=dict)

    def kept_for(self, scorer_name: str) -> bool:
        status = self.scorers.get(scorer_name)
        return status is not None and status.status == "kept"


class ScorerUnavailable(Exception):
    """A scorer could not produce an answer (down, timed out, bad reply).

    Distinct from an answer of "no match": the caller moves on to the next
    scorer instead of spending one of the child's attempts.
    """
