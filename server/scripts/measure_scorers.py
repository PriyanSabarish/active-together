"""Measure a photo-check scorer against a labelled photo set (B54).

Photo set layout (kept outside the repository; these are not child photos):

    <photos>/<prompt_id>/positive/*.jpg     photos that show the prompt
    <photos>/<prompt_id>/negative/*.jpg     near-miss photos that do not

Run from server/, API first, then the hosted CLIP scorer:

    python -m scripts.measure_scorers --scorer api --photos D:/measurement_photos
    python -m scripts.measure_scorers --scorer own_host --photos D:/measurement_photos --write

Without --write the results are printed and nothing is changed. With --write
the per-scorer status (and the CLIP threshold) is written into
content/prompts/vocabulary.yaml.

--scorer api sends the measurement photos to the Gemini API, so it needs
GEMINI_API_KEY and PHOTO_API_ENABLED=true. Use it only with the content
team's measurement photos. --scorer own_host needs INFERENCE_HOST_URL and
INFERENCE_HOST_TOKEN.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.config import settings
from app.photo.measurement import DEFAULT_MIN_CI_LOW, measure_checker, measure_scores, update_vocabulary
from app.photo.scorers import API, OWN_HOST, ApiImageScorer, HostedImageScorer
from app.photo.vocabulary import VOCABULARY_PATH, load_vocabulary

PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png"}


def read_photos(folder: Path) -> list[bytes]:
    if not folder.is_dir():
        return []
    return [p.read_bytes() for p in sorted(folder.iterdir()) if p.suffix.lower() in PHOTO_SUFFIXES]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scorer", choices=[API, OWN_HOST], required=True)
    parser.add_argument("--photos", type=Path, required=True)
    parser.add_argument("--min-ci-low", type=float, default=DEFAULT_MIN_CI_LOW)
    parser.add_argument("--write", action="store_true", help="write results into vocabulary.yaml")
    args = parser.parse_args(argv)

    vocabulary = load_vocabulary()

    if args.scorer == API:
        if not settings.gemini_api_key:
            print("GEMINI_API_KEY is not set.", file=sys.stderr)
            return 2
        from app.gemini_client import GeminiModelClient

        scorer = ApiImageScorer(
            GeminiModelClient(api_key=settings.gemini_api_key, model=settings.gemini_model),
            enabled=settings.photo_api_enabled,
        )
        if not scorer.available():
            print("Set PHOTO_API_ENABLED=true to measure the API scorer.", file=sys.stderr)
            return 2
    else:
        scorer = HostedImageScorer(settings.inference_host_url, settings.inference_host_token)
        if not scorer.available():
            print("The inference host is not configured or not answering.", file=sys.stderr)
            return 2

    results = {}
    for prompt in vocabulary.values():
        folder = args.photos / prompt.id
        positives = read_photos(folder / "positive")
        negatives = read_photos(folder / "negative")
        if not positives and not negatives:
            continue
        if args.scorer == API:
            m = measure_checker(scorer, prompt, positives, negatives, args.min_ci_low)
        else:
            m = measure_scores(prompt, OWN_HOST, scorer.score, positives, negatives, args.min_ci_low)
        results[prompt.id] = {args.scorer: m.status}
        s = m.status
        extra = f" threshold={s.threshold}" if s.threshold is not None else ""
        skipped = f" unanswered={m.skipped}" if m.skipped else ""
        print(
            f"{prompt.id:18} {s.status:8} acc={s.accuracy:.2f} "
            f"[{s.ci_low:.2f}, {s.ci_high:.2f}] n={m.total} ({m.positives}+/{m.negatives}-){extra}{skipped}"
        )

    if not results:
        print("No photo folders matched any prompt id.", file=sys.stderr)
        return 1
    if args.write:
        changed = update_vocabulary(VOCABULARY_PATH, results)
        print(f"Wrote {changed} prompts to {VOCABULARY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
