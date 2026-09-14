"""
generate_missions (B23) — the top-level function A19 calls.

Selection, generation, validation and fallback all happen inside; this
always returns whatever missions it can produce (0 to MAX_MISSIONS), never
raises, and never needs a model running to be tested.

Per candidate template (up to MAX_MISSIONS of them):
  1. Skip it if it fails the schema validator (B21) — malformed content
     never reaches a user regardless of what generation would do with it.
  2. Build the library-direct mission from it (B29/B24) — the version that
     satisfies story 5.1's five-second budget on its own.
  3. If a model_client is given, try rewriting the *variable* steps (see
     the schema's `variable` flag) through it. No response, a timeout, or
     a response that doesn't parse against GENERATION_RESPONSE_SCHEMA all
     fall back to the library-direct wording for that candidate — "retry
     with a different template" (the doc's phrase) means a *different*
     template only kicks in once the current one's own library-direct
     fallback also fails.
  4. Run the result — generated or library-direct — through the safety
     validator (B22). Reject it and move to the next candidate if it
     fails; nothing rejected is ever returned.

model_client is expected to already be configured with
GENERATION_RESPONSE_SCHEMA if it's a GeminiModelClient (B41) — this
function only calls generate_text, it doesn't configure the client.
FixtureModelClient doesn't care since it just returns canned text.

What happens when every candidate is rejected is B30's job, not this
function's — this may return fewer than MAX_MISSIONS, including zero.
"""

from __future__ import annotations

import json
import logging
from typing import Iterable

from app.missions.builder import build_mission
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
) -> list[Mission]:
    candidates = select_templates(
        templates, place, context, age_band, duration_bucket, preferences, recent_template_ids,
    )

    missions: list[Mission] = []

    for template in candidates:
        if len(missions) >= max_missions:
            break

        if not validate_schema(template).ok:
            continue

        library_mission = build_mission(template, age_band, duration_bucket)

        mission = library_mission
        if model_client is not None:
            generated = _try_generate(template, library_mission, place, context, age_band, model_client)
            mission = generated if generated is not None else library_mission

        if not validate_mission(mission, template).ok:
            continue

        missions.append(mission)

    return missions
