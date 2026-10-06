"""Prompt vocabulary loader for photo checks.

Reads server/content/prompts/vocabulary.yaml. Each prompt may carry a
`scorers` mapping written by the B54 measurement:

    scorers:
      api:      {status: kept, accuracy: 0.92, ci_low: 0.81, ci_high: 0.97}
      own_host: {status: kept, threshold: 0.265, accuracy: ..., ci_low: ..., ci_high: ...}

A prompt with no entry for a scorer is a candidate for it, and verify_step()
only uses a scorer on prompts marked kept for that scorer.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.photo.models import Prompt, ScorerStatus

VOCABULARY_PATH = Path(__file__).resolve().parents[2] / "content" / "prompts" / "vocabulary.yaml"


def parse_prompt(entry: dict) -> Prompt:
    scorers = {
        name: ScorerStatus(
            status=value.get("status", "candidate"),
            threshold=value.get("threshold"),
            accuracy=value.get("accuracy"),
            ci_low=value.get("ci_low"),
            ci_high=value.get("ci_high"),
        )
        for name, value in (entry.get("scorers") or {}).items()
    }
    return Prompt(id=entry["id"], text=entry["text"], scorers=scorers)


def load_vocabulary(path: Path = VOCABULARY_PATH) -> dict[str, Prompt]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {entry["id"]: parse_prompt(entry) for entry in raw["prompts"]}
