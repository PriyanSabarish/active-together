"""
generate_missions (B23, B30, B35) — the top-level function A19 calls.

Selection, generation, validation and fallback all happen inside; this
never raises and never needs a model running to be tested.

Per candidate template (up to MAX_MISSIONS of them):
  1. Skip it if it fails the schema validator (B21) — malformed content
     never reaches a user regardless of what generation would do with it.
  2. Build the library-direct mission from it (B29/B24) — the version that
     satisfies story 5.1's five-second budget on its own.
  3. If a model_client is given, try rewriting the *variable* steps (see
     the schema's `variable` flag) through it. No response, a timeout, or
     a response that doesn't parse against GENERATION_RESPONSE_SCHEMA all
     fall back to the library-direct wording for that candidate.
  4. Run the result — generated or library-direct — through the safety
     validator (B22).

Rejection-path exhaustion (B30): if the *generated* rewrite is what got
rejected, the candidate isn't discarded outright — its original,
human-reviewed wording might still be safe, so it's retried once with
pure library-direct text in a second pass, after every candidate has had
a first attempt. A candidate whose library-direct text is itself rejected
is not retried (retrying identical input would just fail identically) and
is dropped for good. If nothing survives either pass, this returns an
empty list — that is the defined behaviour, not an accident, and it's
what Backend A's A25 degrades gracefully around at the API layer.

model_client is expected to already be configured with
GENERATION_RESPONSE_SCHEMA if it's a GeminiModelClient (B41) — this
function only calls generate_text, it doesn't configure the client.
FixtureModelClient doesn't care since it just returns canned text.

Pass a RejectionStats (B35) to count how often generated content gets
rejected, and by which safety constraint — evidence the validator is
doing work, not just an assertion that it does. Library-direct rejections
aren't counted; those would mean the reviewed content itself is unsafe,
which is a content bug, not something the validator catching Gemini
proves.
"""

from __future__ import annotations

import json
import logging
from typing import Iterable

from app.missions.builder import build_mission
from app.missions.instrumentation import RejectionStats
from app.missions.models import MissionTemplate
from app.missions.safety import validate_mission
from app.missions.schema_validator import validate_schema
from app.missions.selector import select_templates
from app.model_client import ModelClient
from app.models import AgeBand, Context, Mission, Place, Step

logger = logging.getLogger(__name__)

MAX_MISSIONS = 3
GENERATION_MAX_TOKENS = 512
GENERATION_TIMEOUT_S = 5  # story 5.1's five-second budget

GENERATION_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "steps": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "sequence": {"type": "INTEGER"},
                    "prompt_text": {"type": "STRING"},
                },
                "required": ["sequence", "prompt_text"],
            },
        },
    },
    "required": ["steps"],
}


def build_generation_prompt(
    template: MissionTemplate,
    place: Place,
    context: Context,
    age_band: AgeBand,
    variable_steps: list[Step],
) -> str:
    """No user data, no identifiers, no image — just place type, weather,
    age band and the theme, per section 1.1's Gemini payload description."""
    weather_bits = []
    if context.available:
        if context.temp_c is not None:
            weather_bits.append(f"{context.temp_c:.0f}°C")
        if context.precip_prob is not None and context.precip_prob >= 0.3:
            weather_bits.append("a chance of rain")
    weather_description = ", ".join(weather_bits) if weather_bits else "weather unavailable"

    steps_block = "\n".join(f"{step.sequence}. {step.prompt_text}" for step in variable_steps)
    place_type = place.activity_category.value.replace("_", " ")

    return (
        f"You are rewriting outdoor activity instructions for a child in the "
        f"{age_band.value} age band, at a {place_type}. Weather: {weather_description}. "
        f"Activity theme: {template.title} ({template.mechanic.value}).\n\n"
        f"Rewrite each numbered step below with fresh wording. Keep the same "
        f"action, difficulty and length — do not add a new hazard or change "
        f"what the child is asked to do:\n{steps_block}\n\n"
        f'Respond as JSON: {{"steps": [{{"sequence": <int>, "prompt_text": "<rewritten text>"}}]}}'
    )


def _variable_steps(template: MissionTemplate, mission: Mission, age_band: AgeBand) -> list[Step]:
    variable_sequences = {
        step.sequence for step in template.bands[age_band].steps if step.variable
    }
    return [step for step in mission.steps if step.sequence in variable_sequences]


def _try_generate(
    template: MissionTemplate,
    base_mission: Mission,
    place: Place,
    context: Context,
    age_band: AgeBand,
    model_client: ModelClient,
) -> Mission | None:
    variable_steps = _variable_steps(template, base_mission, age_band)
    if not variable_steps:
        return base_mission

    prompt = build_generation_prompt(template, place, context, age_band, variable_steps)
    text = model_client.generate_text(prompt, max_tokens=GENERATION_MAX_TOKENS, timeout_s=GENERATION_TIMEOUT_S)
    if text is None:
        return None

    try:
        parsed = json.loads(text)
        rewritten = {item["sequence"]: item["prompt_text"] for item in parsed["steps"]}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        logger.warning("generation response for '%s' did not parse: %s", template.template_id, exc)
        return None

    new_steps: list[Step] = []
    for step in base_mission.steps:
        if step.sequence not in rewritten:
            new_steps.append(step)
            continue

        new_text = rewritten[step.sequence]
        if not isinstance(new_text, str) or not new_text.strip():
            logger.warning("generation response for '%s' had an empty step %s", template.template_id, step.sequence)
            return None

        new_steps.append(step.model_copy(update={"prompt_text": new_text}))

    return base_mission.model_copy(update={"steps": new_steps})


def generate_missions(
    templates: Iterable[MissionTemplate],
    place: Place,
    context: Context,
    age_band: AgeBand,
    duration_bucket: int,
    preferences: Iterable[str] = (),
    recent_template_ids: Iterable[str] = (),
    model_client: ModelClient | None = None,
    max_missions: int = MAX_MISSIONS,
    stats: RejectionStats | None = None,
) -> list[Mission]:
    candidates = select_templates(
        templates, place, context, age_band, duration_bucket, preferences, recent_template_ids,
    )

    missions: list[Mission] = []
    # B30: a candidate whose *generated* rewrite gets rejected isn't
    # necessarily unusable — its original, human-reviewed wording might
    # still be safe. Retry those once with pure library-direct text before
    # giving up on them, rather than discarding on first rejection.
    retry_with_library_direct: list[MissionTemplate] = []

    for template in candidates:
        if len(missions) >= max_missions:
            break

        if not validate_schema(template).ok:
            continue

        library_mission = build_mission(template, age_band, duration_bucket)

        mission = library_mission
        source = "library-direct"
        if model_client is not None:
            generated = _try_generate(template, library_mission, place, context, age_band, model_client)
            if generated is not None:
                mission = generated
                source = type(model_client).__name__

        result = validate_mission(mission, template)
        if stats is not None:
            stats.record(result, was_generated=source != "library-direct")

        if not result.ok:
            if source != "library-direct":
                retry_with_library_direct.append(template)
            continue

        _log_and_append(missions, mission, template, source)

    for template in retry_with_library_direct:
        if len(missions) >= max_missions:
            break

        library_mission = build_mission(template, age_band, duration_bucket)
        if not validate_mission(library_mission, template).ok:
            continue

        _log_and_append(missions, library_mission, template, "library-direct (after generated rejection)")

    return missions


def _log_and_append(
    missions: list[Mission], mission: Mission, template: MissionTemplate, source: str,
) -> None:
    # B42: which client produced this mission, cheap now and the first
    # question asked when mission quality shifts after a provider swap.
    logger.info(
        "mission %s for template '%s' produced by %s",
        mission.mission_id, template.template_id, source,
    )
    missions.append(mission)
