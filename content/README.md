# Content library

## Current integration path: migrated mission families

The 18 activity ideas now have mission families matching Priyan's Step fields
and 20/40/60-minute prefix rule. Start with [the migration handoff](missions/MIGRATION.md).
Run `python content/tools/validate_mission_templates.py --preview` from the repository root.
This checks the migrated collection, including the actual nine safety rules.
All eighteen migrated families are reviewed by lychen, as confirmed by Jiabin.
Timing is still unmeasured; photo vocabulary and runtime integration remain separate work.
The original activity files and independent-duration planner below are retained
as earlier authoring references, not a second current integration contract.

## Activity library foundation v0.1

For the new reusable activity library, start with [activities/README.md](activities/README.md).
Its taxonomy, schema and 18 activity drafts are available for team review, following
the initial 3 integration examples and 6-activity pilot.

    taxonomy/      controlled activity types and proposed subtype mappings
    activities/    one activity family per YAML file, with age variants
    schema/activity_template.schema.yaml    activity JSON Schema, written in YAML
    tools/inspect_location_taxonomy.py      read-only source inventory
    tools/activity_library.py               shared loader and field checks
    tools/validate_activity_templates.py    command-line activity checks
    tools/export_activity_templates.py      reviewed or explicit preview JSON
    examples/activities.preview.json        generated development sample

This is a separate content contract from the existing mission format below.
The existing mission tools do not load or validate activities/. Module 2 provides
a loader and JSON export; the application is not connected yet. Teammates can
start with [activities/INTEGRATION.md](activities/INTEGRATION.md).
Module 3 adds the six-activity pilot and [human review checklist](activities/REVIEW_CHECKLIST.md).
Human approval remains pending; all current activities are development drafts.
Module 4 adds [coverage reporting](activities/COVERAGE.md) and separate
[20/40/60-minute planning estimates](planning/README.md). These estimates are not
measured or approved timings; the existing activity schema and API remain unchanged.

## Existing combo and mission library

Hand-reviewed source of truth for what a family is asked to do. Read this before editing anything here.

## What is in here

    schema/        frozen schema, Pydantic models, safety constraints
    combos/        base combos, one file per activity category
    missions/      mission templates, one file per activity category
    prompts/       candidate prompt vocabulary for measurement

## Status of this batch

Every mission template in `missions/` is `status: draft`. Drafts were produced in bulk to
be edited, not to be shipped. Nothing here may reach a user until:

1. a human other than the author has reviewed it,
2. `review.reviewed_by` is filled in,
3. `status` is changed to `reviewed`.

The safety constraint list in `schema/safety_constraints.yaml` was written by hand and is
inherited by every template. It is never drafted, never generated, and never edited in the
same pull request as a template.

## Category codes are provisional

The seven codes used here are a placeholder set. Replace them with the actual retained
categories from the Vicmap pipeline before authoring at volume. The code is one field on
each file — swapping it is cheap now and expensive after review has started.

## Review checklist

Per template, the reviewer confirms:

- every step is completable after hearing it once, spoken aloud
- no step requires the child to look at a screen
- no step conflicts with any constraint in `safety_constraints.yaml`
- wording is written to the youngest age in the stated band
- steps tagged `verify: photo` use a `prompt_id` that survived measurement
- `site_requirements` is honest — if it needs a playground, say so
- equipment is everyday or empty

## Open question for the team

The prototype shows travel blocks inside a combo ("bike 8 min", "walk home 10 min"), but
acceptance criterion 2.1 says the entered duration is on-site and excludes transport.
Combos here are on-site only, with travel held separately. Settle which is correct before
review, because it changes every combo's block list.

## Bulk drafting workflow

    python tools/coverage.py --target 6          # find the gaps
    python tools/draft_missions.py \
        --category park_and_garden \
        --mechanic move --weather wet --count 4  # fill one gap
    python schema/check_drafts.py                # mechanical rejects
    # human review, then move the family from missions/_candidates/ into missions/<category>.yaml

One gap per batch. Never draft across categories in a single call - the model
converges on one idea and produces four versions of it.

Candidates live in `missions/_candidates/` and are never served. A family only
enters the library when a human other than its author has read every step,
checked it against `schema/safety_constraints.yaml`, filled `review.reviewed_by`
and set `status: reviewed`.
