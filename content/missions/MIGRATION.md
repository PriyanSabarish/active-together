# Mission family integration handoff

Author: Jiabin. Status: all eighteen families reviewed by lychen (confirmed by Jiabin);
timings remain unmeasured. This handoff follows the supplied Iteration 2 Backend
Tasks document: B18 family shape, B29 prefix construction and the Mission/Step
wire fields. It does not implement Backend A endpoints or deploy Backend B.

## Use these files

- `missions/reviewed/activity_*.yaml`: all 18 reviewed migrated families, one per file.
  Each file uses a `templates` list; every family has three bands and seven steps.
- `missions/_candidates/`: reserved for new or revised drafts; currently contains
  no migrated `activity_*.yaml` files. Older unrelated drafts are unchanged.
- `schema/mission_family.validation.yaml`: executable validation companion to
  Priyan's unchanged descriptive `mission_template.schema.yaml`.
- `taxonomy/mission_context_bindings.yaml`: content type, candidate place categories,
  unbound preference codes and essential parent briefings, separate from the family.
- `tools/mission_library.py`: family loading, `build_mission` and final-step checks.
- `examples/mission_families.reviewed.json`: reviewed-mode export of all 18 families
  and content bindings. Review does not certify timing or complete runtime integration.
- `examples/mission_families.preview.json`: development-mode export, currently with
  the same 18 reviewed families; future drafts may appear only in this mode.
- `examples/mission.preview.json`: a 20-minute, 5-7 Colour Hunt wire-shape sample
  inside a clearly marked development envelope.

The migration IDs are `activity_` plus the original activity ID. Original
`activities/` files and their JSON/planner are retained as authoring references,
not the active backend handoff. Do not load both as separate recommendations.
Priyan's older mission category files are unchanged and are outside this new
loader's collection. This does not replace the 21 base combos or prove category coverage.

## Install and run

From the repository root, with Python 3.10+:

```text
python -m pip install -r content/requirements.txt
python content/tools/validate_mission_templates.py --preview
python content/tools/validate_mission_templates.py
python content/tools/export_mission_templates.py --output content/examples/mission_families.reviewed.json
python content/tools/export_mission_templates.py --preview --output content/examples/mission_families.preview.json
python content/tools/export_mission_templates.py --preview --template-id activity_colour_hunt --age-band 5-7 --duration 20 --output content/examples/mission.preview.json
python -m unittest discover -s content/tests -v
```

Current preview: 18 families, 54 age variants, 162 age/bucket combinations.
Current reviewed collection: 18 families, 54 age variants, 162 age/bucket combinations.
Without `--preview`, the exporter never returns
drafts and an unavailable requested template produces an error, not a substitute.

After independent review, move the approved family from `_candidates/` into
`missions/reviewed/`, retain its filename, and set its reviewer and reviewed status.
There must be one copy of each ID. Publish only a reviewed-mode export.
Neither the loader nor the reviewer-name check proves that a person performed review.

## Step and duration contract

`build_mission(template, band, duration_bucket)` uses the requested band's first
3, 5 or 7 authored steps for 20, 40 or 60. All steps carry `sequence`, `prompt_text`,
`verify_mode` and `prompt_id`. The authoring flag `variable: true` is omitted from
the returned Step, as specified in the backend document.

Steps 1-3 form the first game; 4-5 and 6-7 are additional complete rounds or
variations. Reviewers must test all three stopping points. Automated step counts
cannot establish completeness, enjoyment or appropriate difficulty.
The three bands are rewritten tasks, not just expanded vocabulary. The youngest
instructions are strictly under 12 words.

The returned `estimated_minutes` is the backend bucket label, not a measured
duration. The envelope explicitly states `backend_step_count_contract_not_measured`.
Do not promise that seven short instructions occupy an hour. The older optional-round
duration planner must not be combined with this truncation rule.
The local builder gives a deterministic `preview_...` mission ID for fixtures.
Backend B must allocate its real mission/session IDs when integrating it.

## Photo verification

All 378 authored steps currently use `verify_mode: self` and `prompt_id: null`.
The real prompt vocabulary still has no measured kept entries. Content must not
promote a candidate to kept, fabricate a threshold, or mark an activity photo-ready
merely to demonstrate the interface.

For `photo`, the checker requires a known `prompt_id` with status `kept`; unknown,
candidate and dropped prompts fail. For `self`, `prompt_id` must be null. Tests
exercise a photo family with a fixture-local kept vocabulary. That fixture is
not exported or loaded as real content and is not measurement evidence.
Backend B owns B25 measurement, B26 thresholds and B34 vocabulary maintenance.
When results arrive, choose only steps whose actual task matches a measured
visual target. An arbitrary colour choice cannot be hard-coded as `p_red`.
Actions, sounds and completion over time cannot be established by a still image.

## Safety checking and its limits

`mission_checks.py` reads the actual nine rules from `safety_constraints.yaml`.
The rule file has not been changed. Missing or malformed rules fail loading.
All nine have rejection fixtures tested against both authored families and
rewritten Mission steps. Checks also reject filler and flag suspicious facility
references. A final Mission with such unresolved warnings is not accepted by
the local `validate_mission` helper. That conservative helper has no facility
verification evidence with which to clear a warning.

Phrase checks use word boundaries, punctuation tolerance and common verb forms.
This avoids `repeat the` accidentally matching `eat the`, or `signal` matching
`sign`. No blanket exception is made for negated instructions.
These remain coarse checks, not general language understanding: paraphrased
hazards, inappropriate difficulty, subtle invention and prompt-to-image meaning
still require review and Backend B's full B21/B22 integration.

The supplied `validate_mission(mission, template)` returns `ok`, `failures` and
`warnings`. It checks the wire shape, exact age/bucket support, sequence and
verification metadata, then scans rewritten steps. Backend B must call validation
after generation and on the library-direct path, before display; a source review
does not approve future generated text. This helper is not wired into the server.

The old `schema/check_drafts.py` now dispatches the migrated collection to these
checks. Its broader legacy run still reports three pre-existing word-limit errors
in `tree_observations` (5-7 steps 1, 3, 5). A read-only comparison against the HEAD
checker without migrated files reproduced those same three errors. Older batches
and their review/measurement warnings were not repaired in this migration.

## Parent guidance and material content changes

The existing family/wire shape has no setup or parent-guidance field. Essential
briefings are therefore preserved in the separate content bindings and included
in both exports. The receiving app must show the matching briefing before play
and keep adult supervision and stopping/skip choices available throughout. Do not
strip bindings and serve only steps without supplying that guidance elsewhere.
The wire Mission has not been silently extended; the briefing delivery location
remains a Backend B/Client integration responsibility.

Two original equipment-dependent ideas were adapted to the existing everyday
equipment allowlist: Sort and Step now groups spoken object names rather than
picture cards; Roll to Target now rolls towards the adult's waiting hands rather
than a cloth target. Fifteen migrated families require no equipment and three
require a family-supplied soft ball. Review these changed mechanics explicitly.
Original source steps and parent prompts are not mechanically copied into the new
rounds; the entire migrated family needs its own review.

## Responsibilities still outside this change

- Backend B: real service and model client, measured photo vocabulary/thresholds,
  runtime validation and fallback, selection/ranking, final mission IDs.
- Backend A and Client: endpoints, parent briefing display, request/response
  integration, photo privacy, retry/manual flow and offline behavior.
- Team review: three stopping points in every band, site requirements, usefulness,
  real timing observations and the consolidated AI usage statement.

See [CONTEXT.md](CONTEXT.md) for location, weather, air-quality and preference
preparation, and [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md) for the unapproved queue.
