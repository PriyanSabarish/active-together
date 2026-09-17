"""
RejectionStats (B35) — turns "the validator rejects unsafe missions" into a
number: "it rejected 4.2% of generations, most often on the stay-in-sight
rule." Counts only the generation path, not library-direct servings — a
library-direct rejection would mean the reviewed content itself is unsafe,
which is a content bug, not evidence the safety validator is earning its
keep against model output.

A caller creates one long-lived RejectionStats and passes it into every
generate_missions call so counts accumulate across the app's lifetime;
tests create a fresh one per test instead of relying on global state.
"""

from __future__ import annotations

import re
from collections import Counter

from app.missions.models import ValidationResult

_CONSTRAINT_PATTERN = re.compile(r"violates (?P<constraint_id>\w+) —")


class RejectionStats:
    def __init__(self) -> None:
        self.generation_attempts = 0
        self.generation_rejections = 0
        self.by_constraint: Counter[str] = Counter()

    def record(self, result: ValidationResult, *, was_generated: bool) -> None:
        if not was_generated:
            return

        self.generation_attempts += 1
        if result.ok:
            return

        self.generation_rejections += 1
        for failure in result.failures:
            match = _CONSTRAINT_PATTERN.search(failure)
            if match:
                self.by_constraint[match.group("constraint_id")] += 1

    @property
    def rejection_rate(self) -> float:
        if self.generation_attempts == 0:
            return 0.0
        return self.generation_rejections / self.generation_attempts
