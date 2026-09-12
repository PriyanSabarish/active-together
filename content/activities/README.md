# Activity library foundation

Integration notice: these files are retained as original authoring references.
Use the [migrated mission families](../missions/MIGRATION.md) for the agreed backend
format, verification hooks and safety checks. Do not promote both representations.
The module history below describes the earlier activity contract.

Modules 1-4 deliver a content contract, source-grounded taxonomy mapping,
18 activity drafts, a loader, JSON export, coverage report and a human review checklist.
Start integration with [INTEGRATION.md](INTEGRATION.md). The initial six-activity
pilot remains the first review priority. Deploy only the subset that has passed
human review and integration checks.

## Start here

- `../taxonomy/activity_types.yaml`: six proposed activity types and mechanic IDs.
- `../taxonomy/subtype_activity_mapping.yaml`: all 16 retained subtype combinations.
- `../schema/activity_template.schema.yaml`: executable JSON Schema written in YAML.
- `_candidates/follow_the_leader.yaml`: one activity with three age variants.
- `_candidates/colour_hunt.yaml`: observation play with three age variants.
- `_candidates/pass_and_move.yaml`: ball play with three age variants and required equipment.
- `_candidates/balance_shapes.yaml`: grounded balance and controlled transitions.
- `_candidates/notice_the_change.yaml`: observation and memory of pose changes.
- `_candidates/imaginary_delivery.yaml`: pretend play, including a four-step age variant.
- `../examples/activities.preview.json`: generated sample containing all 18 drafts.
- `COVERAGE.md`: generated counts by activity type, age and proposed subtype mapping.
- `../planning/README.md`: separate draft duration profiles and combo preview instructions.
- `REVIEW_CHECKLIST.md`: per-activity review queue and deployment handoff checks.
- `source_inventory.md`: exact dataset version, counts and branch differences.
- `reviewed/`: approved activity files only; currently empty of activities.

Use UTF-8, two-space indentation and quoted age-band keys. One YAML file holds
one activity family. Its filename equals `activity_id`. Source content is English;
translation can be added later without changing activity IDs.

For activities in Jiabin's authoring workstream, use `review.author: Jiabin`.
Keep `reviewed_by: null` and `status: draft` until independent human review.
AI assistance with structure, drafting and checks will be documented in a
consolidated AI usage statement before final handoff; that statement is pending.

## Three different concepts

| Field | Meaning | Example |
| --- | --- | --- |
| `activity_category` | Existing place category; appears only in the mapping | `court` |
| `activity_type` | Primary type of play; defined in the activity taxonomy | `movement_play` |
| `activity_id` | Stable identity of a specific game | `follow_the_leader` |
| `core_mechanic` | Main rule that makes the game work | `imitate` |

Each activity has one primary type and one main mechanic. Related experiences
do not require duplicate activities or extra tags. A movement game with an animal
title stays movement_play; use imaginative_play when pretending drives its rules.
The initial six types are a small authoring vocabulary, not a promise that each
type has content ready. Add types only when a genuinely different game needs one.

## Field contract v0.1

All top-level fields below are required. Empty equipment and adaptation lists
are valid; requirements, setup, constraints and steps must contain actual text.

| Field | What an author writes |
| --- | --- |
| `schema_version` | `"0.1.0"`; identifies the data contract |
| `activity_id` | Stable snake_case ID; not a title, age or duration |
| `version` | Positive integer; increase when content changes after review |
| `title`, `summary` | Name and short explanation of the core game |
| `activity_type` | One ID from `activity_types.yaml` |
| `core_mechanic` | One ID from its `core_mechanics` list |
| `participation` | Minimum children, minimum adults and the adult's role |
| `equipment` | Required and optional items; optional items cannot be necessary to finish |
| `requirements` | Preconditions to check, not claims about a mapped place |
| `setup` | Preparation shared by all supported age variants |
| `age_variants` | At least one of `"5-7"`, `"8-10"`, `"11-12"`; target all three where appropriate |
| `age_variants.<band>.challenge` | What changes about the task at this age |
| `age_variants.<band>.steps` | Ordered list of `step_id`, `instruction`, `parent_prompt` |
| `age_variants.<band>.ending` | Standalone way to finish this activity |
| `adaptations` | Allowed simplifications and extensions within the existing constraints |
| `constraints` | Boundaries retained by future selection and story composition |
| `safety_reference` | `schema/safety_constraints.yaml`, relative to `content/` |
| `review` | Author, reviewer or null, and draft/reviewed status |

Array order is execution order. Do not add a second sequence number to maintain.
Step IDs are unique within each age variant. Unsupported age bands are omitted;
the selector does not substitute another age band. Older variants change
the task, not just vocabulary. These bands are provisional content adaptations,
not evidence of developmental suitability.

The YAML schema checks field shapes, required values and reviewer presence.
The shared loader also checks type/mechanic membership, duplicate activity and
step IDs, filenames and review status. It rejects matching author/reviewer names
after normalising case and whitespace; people must verify reviewer independence.
Meaningful age differences, suitability and safety still require human review.
Existing `schema/check_drafts.py` is for missions only.

## Location mapping boundary

Mappings use the exact `(activity_category, feature_type, feature_subtype)` triple.
`candidate_activity_types` is a planning shortlist. It does not grant permission
to use a site, provide equipment, or prove any activity is eligible. Requirements
still apply, even for equipment-free activities. No automatic bare-site fallback
is defined; unknown triples have no mapping. Cycling and skating are separate
games within wheeled_play and are not interchangeable.

This module records relationships but implements no location matching or ranking.
Names enriched from council sources must not be used to infer extra facilities.

## Handoff to the application

Module 2 loads YAML and returns ordinary JSON-compatible values, preserving
the field names above. The export envelope includes an explicit mode:

```json
{
  "schema_version": "0.1.0",
  "mode": "reviewed",
  "activities": []
}
```

Each item in `activities` will be a complete record matching the activity schema.
The initial reviewed export is empty because no activity has human approval yet.
The explicit development preview includes drafts and labels the envelope
`mode: development_preview`. Production consumers must require `mode: reviewed`.
This is a file/data contract, not a new API endpoint. Default loading reads only
`reviewed/` and rejects invalid records or missing review; candidate files are
never a production fallback. Files use `.yaml` by convention; the loader also
checks `.yml` files. All selected files are validated before filtering or export.

## Duration and future stories

No duration, weather, preference, photo verification or AI service fields are
part of the activity v0.1 contract. Module 4 keeps unmeasured duration estimates
in `../planning/duration_profiles.yaml`, keyed by activity ID, version and age.
Combo budgets are 20/40/60 minutes. Preview planning reports unused time or
over-budget combinations instead of changing the authored core steps.

For Iteration 3, a combo can reference 2-3 activities by ID, version and age band.
Story wording may supply an introduction, transitions and an ending, while keeping
each activity's tasks, equipment, preconditions and constraints. Activities must
stand alone and never refer to an unnamed previous task. This is a design boundary,
not an implemented AI control or story-generation feature.
