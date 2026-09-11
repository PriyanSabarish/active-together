# Activity samples for teammate integration

The module 4 library supplies 18 draft activities and 54 age variants. You can use them
now to debug reading, filtering, cards, steps and an explicit group of activities.
No Groq key, database, backend server or network request is needed to load them.
Production deployment of this content still needs independent human review.

## Quick start

Use Python 3.10+ and run these commands from the repository root, preferably in
your existing development environment:

```text
python -m pip install -r content/requirements.txt
python content/tools/validate_activity_templates.py --preview
python content/tools/export_activity_templates.py --preview --output content/examples/activities.preview.json
```

Expected validation: `Valid development preview: 18 activities, 54 age variants.`
The generated file is included with the samples, so frontend teammates
can read it directly without installing Python. Regenerate it whenever sample
YAML changes; it is a development fixture, not a second authoring source.
The export command replaces the requested JSON file only after validation passes.

| Activity ID | Type | Equipment | Age variants |
| --- | --- | --- | --- |
| `balance_shapes` | `movement_play` | None | 5-7, 8-10, 11-12 |
| `colour_hunt` | `exploration_play` | None | 5-7, 8-10, 11-12 |
| `follow_the_leader` | `movement_play` | None | 5-7, 8-10, 11-12 |
| `imaginary_delivery` | `imaginative_play` | None | 5-7, 8-10, 11-12 |
| `notice_the_change` | `exploration_play` | None | 5-7, 8-10, 11-12 |
| `pass_and_move` | `ball_play` | Soft ball for rolling | 5-7, 8-10, 11-12 |

The table above identifies the original six pilot examples. The preview also
contains twelve expansion drafts; see [COVERAGE.md](COVERAGE.md) for current counts
and [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md) for their names and review queue.
Type and age filtering can now return more matches; do not hard-code result counts.

Each variant has a challenge, ordered steps and an ending. Most have three steps;
Imaginary Delivery for 11-12 has four. Consumers must handle any positive step count.
Use `equipment.required`, `requirements` and `participation` when displaying the
preparation information. A category mapping does not establish these conditions.

## Two entry points

| Entry | Loaded content | Export mode |
| --- | --- | --- |
| Default | Validated files in `activities/reviewed/` only | `reviewed` |
| `--preview` | Reviewed files plus `_candidates/` drafts | `development_preview` |

```text
python content/tools/validate_activity_templates.py
python content/tools/export_activity_templates.py
```

These currently report zero reviewed activities and an empty `activities` list.
This is expected, not a missing-data error. Production callers must handle an
empty list and must never substitute the preview file. A production JSON consumer
must explicitly require `mode == "reviewed"` before displaying activities.

The mode field is module 2's added envelope metadata; activity fields remain at
schema version `0.1.0`. The full format is:

```json
{
  "schema_version": "0.1.0",
  "mode": "development_preview",
  "activities": []
}
```

The example above shows the envelope only; the supplied preview file contains
18 complete records. Records are sorted by `activity_id` for reproducible
exports. This ordering is not a recommendation ranking.

## Python integration

From project-root Python code, import the module directly:

```python
from content.tools.activity_library import (
    load_preview_activities,
    load_reviewed_activities,
    select_activities,
)

# Development only. Production code calls load_reviewed_activities().
activities = load_preview_activities()
matches = select_activities(activities, activity_type="ball_play", age_band="8-10")

if matches:
    activity = matches[0]
    variant = activity["age_variants"]["8-10"]
    for step in variant["steps"]:
        print(step["instruction"], step["parent_prompt"])
    print(variant["ending"])
```

Filtering preserves complete records and all their age variants. After selection,
the consumer reads the exact requested age key. An unsupported or absent age
must not be replaced by another band. Unknown types return an empty list; invalid
age-band values raise `ValueError`. A valid but unwritten age band simply removes
that activity from the matches. No age or type filter returns the whole library.

Command-line equivalent:

```text
python content/tools/export_activity_templates.py --preview --activity-type ball_play --age-band 8-10
```

Without `--output`, stdout is JSON only. Source paths are based on the script's
location, so an absolute script path works from any directory. Relative output
paths, however, are relative to your current working directory.

## JavaScript integration and a small combo fixture

Read or import `content/examples/activities.preview.json` through your development
tooling. Do not automatically publish this file under the production client assets.
The following function works with the already parsed JSON object:

```javascript
// Build a development-only group of chosen activities in the caller's order.
function buildComboPreview(library, activityIds, ageBand) {
  if (library.mode !== "development_preview") {
    throw new Error("This helper expects the development sample library.");
  }
  const items = activityIds.map((id) => {
    const activity = library.activities.find((item) => item.activity_id === id);
    if (!activity || !activity.age_variants[ageBand]) {
      throw new Error(`Activity or age variant unavailable: ${id} / ${ageBand}`);
    }
    return { activity, variant: activity.age_variants[ageBand] };
  });
  return { mode: "development_preview", age_band: ageBand, items };
}

const combo = buildComboPreview(
  library,
  ["follow_the_leader", "colour_hunt", "pass_and_move"],
  "8-10"
);
```

This example lets you render two or three explicitly selected activities while
keeping each activity's preparation, requirements, constraints and ending.
It is not a timed recommendation, story generator or replacement for the
backend's existing Combo response. Later, references should retain activity ID,
version and age band so the selected content can be identified precisely.

## Errors and checks

The loader rejects malformed YAML (including duplicate field names), invalid
schema fields, unknown type/mechanic IDs, duplicate activity/step IDs, filename
mismatches and review-state violations. Errors name the affected file where
applicable. Nothing is silently skipped. Invalid selected content fails before
filtering, so a filter cannot hide a broken record. Reviewed loading never reads
the candidate directory, including when a candidate is malformed.

```text
python -m unittest discover -s content/tests -v
```

Tests cover reviewed/preview isolation, promotion rules, exact-age filtering,
invalid records, command-line output and reproducibility of the supplied JSON.
Structural checks do not assess real-world suitability, fun, age appropriateness
or actual reviewer identity. Those remain team review responsibilities.

## Current scope

Teammates can begin content/UI integration after this module is pushed to the
shared branch. Module 4's content and technical checks are ready; independent
human review is pending in [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md).
Separate [duration planning](../planning/README.md) now provides a development
timetable for chosen IDs, with unmeasured estimates and explicit unused-time states.
Place matching, preferences, weather, verification, production timed recommendation,
runtime API integration and AI stories are not implemented by this package. All 18
authors are recorded as Jiabin; the consolidated AI usage statement remains to
be written before final handoff.
