"""
Manual smoke test for GeminiModelClient (B37/B41) — NOT part of the
automated suite. It costs a fraction of a cent and needs a live
GEMINI_API_KEY in .env, so it must never run in CI; run it by hand:

    python scripts/verify_gemini.py

Confirms things the mocked test suite can't: that the real Gemini API
response shape matches what GeminiModelClient assumes, that a full
generate_missions call with structured output produces usable rewritten
mission text end to end, and — as of the reviewed-library fix — that the
*actual* real content (content/missions/reviewed/, 18 families, all
category "any") is selectable through the real eligible_categories
bindings, not just fixtures.

Every per-template detail (place, band, bucket) is derived from the
template itself via _generate_and_print — never hardcoded a second time
nearby — because this script gets edited directly to try different
fixtures/bands, and hardcoding the same fact twice is exactly what kept
going stale here. To test a specific band, pass it explicitly to
_generate_and_print for a template that actually has that band —
mfx.MULTI_BAND_FAMILY is the one fixture with all three (5-7, 8-10,
11-12); most others only have one.

_place_matching resolves a place two ways: a template with a specific
(non-"any") category is matched directly against ActivityCategory — this
is only ever true for old fixtures/superseded content now, since every
real reviewed family is category "any". For "any" templates, it looks up
eligible_place_categories in the real bindings file (content/taxonomy/
mission_context_bindings.yaml) and picks a fixture place matching one of
them; with no binding at all it's treated as unbound (any place works,
same as select_templates itself does). Either way, if nothing matches,
_generate_and_print falls back to generation directly (build_mission +
_try_generate, bypassing select_templates), clearly labelled, rather than
crashing or silently skipping it — this is how the 4 categories with no
real ActivityCategory equivalent (in the old, superseded top-level
content/missions/*.yaml files) get exercised too.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.gemini_client import GeminiModelClient
from app.missions.builder import build_mission
from app.missions.context_bindings import load_eligible_categories
from app.missions.generation import GENERATION_RESPONSE_SCHEMA, _try_generate, generate_missions
from app.missions.loader import load_template_dir
from app.models import ActivityCategory, AgeBand
from tests import fixtures
from tests import mission_fixtures as mfx


def _place_matching(template, eligible_categories: dict[str, list[str]]):
    if template.category != "any":
        try:
            return next(p for p in fixtures.DENSE_INNER if p.activity_category == ActivityCategory(template.category))
        except (ValueError, StopIteration):
            return None

    bound = eligible_categories.get(template.template_id)
    if not bound:
        return fixtures.DENSE_INNER[0]

    return next((p for p in fixtures.DENSE_INNER if p.activity_category.value in bound), None)


def _first_band(template) -> AgeBand:
    return next(iter(template.bands))


def _generate_and_print(
    template, band: AgeBand, structured_client: GeminiModelClient,
    eligible_categories: dict[str, list[str]] | None = None,
) -> None:
    eligible_categories = eligible_categories or {}
    print(f"--- {template.template_id} ({template.title}), category={template.category}, band={band.value} ---")
    print("Original steps:")
    for step in template.bands[band].steps:
        print(f"  {step.sequence}. {step.prompt_text}")

    place = _place_matching(template, eligible_categories)

    if place is not None:
        print(f"Place: {place.display_name} ({place.activity_category.value})")
        missions = generate_missions(
            [template], place, fixtures.CLEAR_MILD, band, template.duration_bucket,
            model_client=structured_client, eligible_categories=eligible_categories,
        )
        if not missions:
            print("FAILED: generate_missions returned nothing (selection or validation failed)")
            return
        mission = missions[0]
        print(f"Generated mission {mission.mission_id}:")
        for step in mission.steps:
            print(f"  {step.sequence}. {step.prompt_text}  [{step.verify_mode.value}]")
    else:
        print("No matching place found (no ActivityCategory equivalent, or bound to categories")
        print("with no matching fixture place) — select_templates would never reach this;")
        print("testing generation directly instead:")
        library_mission = build_mission(template, band, template.duration_bucket)
        dummy_place = fixtures.DENSE_INNER[0]
        generated = _try_generate(template, library_mission, dummy_place, fixtures.CLEAR_MILD, band, structured_client)
        if generated is None:
            print("FAILED: generation failed / fell back to None")
            return
        print("Generated (via direct generation):")
        for step in generated.steps:
            print(f"  {step.sequence}. {step.prompt_text}  [{step.verify_mode.value}]")


def step1_raw_call(client: GeminiModelClient) -> bool:
    print("=== Step 1: raw generate_text call ===")
    text = client.generate_text("Say hello in one short sentence.", max_tokens=32, timeout_s=10)
    print("Response:", repr(text))
    if text is None:
        print("FAILED: got None back — check the key, model name, or network.")
        return False
    return True


def step2_fixture_mission(structured_client: GeminiModelClient) -> None:
    print("\n=== Step 2: structured-output generate_missions call (fixture) ===")
    # Edit these two lines to try a different template/band. MULTI_BAND_FAMILY
    # has all three bands, so it's the one safe to override `band` freely on.
    template = mfx.MULTI_BAND_FAMILY
    band = AgeBand.BAND_8_10
    _generate_and_print(template, band, structured_client)


def step3_real_reviewed_library(structured_client: GeminiModelClient) -> None:
    print("\n=== Step 3: every real reviewed family, with real category bindings ===")
    templates = load_template_dir()  # content/missions/reviewed/, the real library
    bindings = load_eligible_categories()  # content/taxonomy/mission_context_bindings.yaml
    print(f"Loaded {len(templates)} reviewed families, {len(bindings)} category bindings\n")

    for template in templates:
        _generate_and_print(template, _first_band(template), structured_client, eligible_categories=bindings)
        print()


def main() -> None:
    if not settings.gemini_api_key:
        print("GEMINI_API_KEY is not set in .env — nothing to test.")
        return

    print(f"Using model: {settings.gemini_model}\n")

    plain_client = GeminiModelClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if not step1_raw_call(plain_client):
        return

    structured_client = GeminiModelClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        response_schema=GENERATION_RESPONSE_SCHEMA,
    )
    step2_fixture_mission(structured_client)
    step3_real_reviewed_library(structured_client)


if __name__ == "__main__":
    main()
