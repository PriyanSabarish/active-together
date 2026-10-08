"""Scorer measurement (B54).

For each prompt and scorer, run a positive set (photos that show it) and a
near-miss negative set (photos that look like it but do not, such as a green
bin for "something green") and report accuracy with a Wilson interval. The
decision whether a prompt is kept uses the interval's lower bound, never the
point estimate, so a small sample cannot flatter a prompt.

CLIP also needs a per-prompt threshold. It is fitted here from the measured
scores. A prompt that cannot reach the bar is dropped for that scorer; it is
never kept with a lower threshold (B57).

The threshold is fitted on the same photos it is then scored on, which is
optimistic. Run the measurement on a photo set held apart from any set used to
tune prompts, and report that caveat with the numbers.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import yaml

from app.photo.models import Prompt, ScorerStatus, ScorerUnavailable
from app.photo.scorers import API, OWN_HOST, ImageScorer

# Lower bound of the Wilson interval a prompt must reach to be kept. This is a
# working default pending a decision from the team; pass min_ci_low to change it.
DEFAULT_MIN_CI_LOW = 0.80
MIN_PER_SET = 10  # fewer photos than this in either set and the prompt is dropped
KNOWN_SCORERS = (OWN_HOST, API)


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion. (0, 1) when n is 0."""
    if n <= 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


@dataclass(frozen=True)
class PromptMeasurement:
    prompt_id: str
    scorer: str
    true_positive: int
    positives: int
    true_negative: int
    negatives: int
    status: ScorerStatus
    skipped: int = 0  # photos the scorer could not answer; counted as wrong

    @property
    def correct(self) -> int:
        return self.true_positive + self.true_negative

    @property
    def total(self) -> int:
        return self.positives + self.negatives


def _decide(
    correct: int,
    total: int,
    positives: int,
    negatives: int,
    min_ci_low: float,
    threshold: float | None,
) -> ScorerStatus:
    low, high = wilson_interval(correct, total)
    accuracy = correct / total if total else 0.0
    enough = positives >= MIN_PER_SET and negatives >= MIN_PER_SET
    kept = enough and low >= min_ci_low
    return ScorerStatus(
        status="kept" if kept else "dropped",
        threshold=threshold if kept else None,
        accuracy=round(accuracy, 4),
        ci_low=round(low, 4),
        ci_high=round(high, 4),
    )


def measure_checker(
    scorer: ImageScorer,
    prompt: Prompt,
    positives: Sequence[bytes],
    negatives: Sequence[bytes],
    min_ci_low: float = DEFAULT_MIN_CI_LOW,
) -> PromptMeasurement:
    """Measure a scorer that answers yes/no (the API scorer).

    The prompt is checked as if kept for this scorer, since measuring is what
    decides that.
    """
    probe = Prompt(prompt.id, prompt.text, {**prompt.scorers, scorer.name: ScorerStatus("kept")})
    tp = tn = skipped = 0
    for photo in positives:
        try:
            tp += scorer.check(photo, probe)
        except ScorerUnavailable:
            skipped += 1
    for photo in negatives:
        try:
            tn += not scorer.check(photo, probe)
        except ScorerUnavailable:
            skipped += 1
    # A photo the scorer could not answer counts as wrong: neither tp nor tn
    # grows, while the totals still include it.
    status = _decide(tp + tn, len(positives) + len(negatives), len(positives), len(negatives), min_ci_low, None)
    return PromptMeasurement(prompt.id, scorer.name, tp, len(positives), tn, len(negatives), status, skipped)


def fit_threshold(positive_scores: Sequence[float], negative_scores: Sequence[float]) -> tuple[float, int]:
    """Threshold with the most correct photos; ties go to the higher (stricter) one.

    A photo confirms when score >= threshold. Candidates are the observed
    scores. Returns (threshold, correct count).
    """
    candidates = sorted(set(positive_scores) | set(negative_scores))
    best_threshold, best_correct = candidates[0], -1
    for t in candidates:
        correct = sum(s >= t for s in positive_scores) + sum(s < t for s in negative_scores)
        if correct >= best_correct:
            best_threshold, best_correct = t, correct
    return best_threshold, best_correct


def measure_scores(
    prompt: Prompt,
    scorer_name: str,
    score: Callable[[bytes, str], float],
    positives: Sequence[bytes],
    negatives: Sequence[bytes],
    min_ci_low: float = DEFAULT_MIN_CI_LOW,
) -> PromptMeasurement:
    """Measure a scorer that gives a similarity (CLIP) and fit its threshold."""
    pos = [score(photo, prompt.text) for photo in positives]
    neg = [score(photo, prompt.text) for photo in negatives]
    if not pos or not neg:
        status = _decide(0, len(pos) + len(neg), len(pos), len(neg), min_ci_low, None)
        return PromptMeasurement(prompt.id, scorer_name, 0, len(pos), 0, len(neg), status)
    threshold, correct = fit_threshold(pos, neg)
    tp = sum(s >= threshold for s in pos)
    tn = sum(s < threshold for s in neg)
    status = _decide(correct, len(pos) + len(neg), len(pos), len(neg), min_ci_low, round(threshold, 4))
    return PromptMeasurement(prompt.id, scorer_name, tp, len(pos), tn, len(neg), status)


# Writing results into vocabulary.yaml

_ENTRY = re.compile(r"^(\s*)- (\{id: (\w+),.*\})\s*$")


def overall_status(scorers: dict[str, dict]) -> str:
    """Top-level status the mission checks read: kept if any scorer kept it."""
    statuses = [scorers.get(name, {}).get("status", "candidate") for name in KNOWN_SCORERS]
    if "kept" in statuses:
        return "kept"
    if all(s == "dropped" for s in statuses):
        return "dropped"
    return "candidate"


def _status_dict(status: ScorerStatus) -> dict:
    entry = {"status": status.status}
    for key in ("threshold", "accuracy", "ci_low", "ci_high"):
        value = getattr(status, key)
        if value is not None:
            entry[key] = value
    return entry


def update_vocabulary(
    path: Path,
    results: dict[str, dict[str, ScorerStatus]],
) -> int:
    """Write per-scorer status into vocabulary.yaml, line by line.

    Only the prompt lines named in results are rewritten, so comments and the
    rest of the file stay as they are. Returns how many prompts changed.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = 0
    for i, line in enumerate(lines):
        match = _ENTRY.match(line.rstrip("\r\n"))
        if not match or match.group(3) not in results:
            continue
        entry = yaml.safe_load(match.group(2))
        scorers = dict(entry.get("scorers") or {})
        for name, status in results[match.group(3)].items():
            scorers[name] = _status_dict(status)
        entry["scorers"] = scorers
        entry["status"] = overall_status(scorers)
        dumped = yaml.safe_dump(entry, default_flow_style=True, sort_keys=False, width=10**6).strip()
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        lines[i] = f"{match.group(1)}- {dumped}{newline}"
        changed += 1
    path.write_text("".join(lines), encoding="utf-8", newline="")
    return changed
