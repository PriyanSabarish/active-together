from __future__ import annotations

from dataclasses import dataclass, fields
import json
from pathlib import Path
from typing import Final

from app.models import Context

CONFIG_PATH = Path(__file__).parent / "thresholds.json"

DEPRIORITISE: Final[str] = "deprioritise"
REMIND: Final[str] = "remind"
VALID_EFFECTS: Final[frozenset[str]] = frozenset({DEPRIORITISE, REMIND})
CONTEXT_FIELDS: Final[frozenset[str]] = frozenset(f.name for f in fields(Context))


@dataclass(frozen=True)
class Threshold:
    field: str
    value: float
    effect: str
    message: str
    source: str

    def triggers(self, reading: float | None) -> bool:
        return reading is not None and reading >= self.value


def load_thresholds(path: Path = CONFIG_PATH) -> tuple[Threshold, ...]:
    raw_config = json.loads(path.read_text(encoding="utf-8"))
    if not raw_config:
        raise ValueError(f"No thresholds defined in {path}")

    thresholds: list[Threshold] = []
    for field_name, entry in raw_config.items():
        if field_name not in CONTEXT_FIELDS:
            raise ValueError(
                f"Threshold '{field_name}' is not a field on Context. "
                f"Valid fields: {', '.join(sorted(CONTEXT_FIELDS))}"
            )

        if entry["effect"] not in VALID_EFFECTS:
            raise ValueError(
                f"Threshold '{field_name}' has invalid effect '{entry['effect']}'. "
                f"Must be one of: {', '.join(sorted(VALID_EFFECTS))}"
            )

        thresholds.append(
            Threshold(
                field=field_name,
                value=float(entry["value"]),
                effect=entry["effect"],
                message=entry["message"],
                source=entry["source"],
            )
        )

    return tuple(thresholds)


THRESHOLDS: tuple[Threshold, ...] = load_thresholds()