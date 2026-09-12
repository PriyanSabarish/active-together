# Duration planning for the activity library

Historical planning experiment: the current handoff follows Priyan's 3/5/7-step
mission contract; see [the migration guide](../missions/MIGRATION.md). Do not combine
this planner's optional rounds with the migrated mission prefixes. Its unmeasured
timing estimates are not evidence for the new 20/40/60-minute labels.

The team chose 20, 40 and 60 minutes as combo budgets. Module 4 keeps the existing
activity schema and export unchanged and adds a separate draft timing configuration.
No location ranking, weather, preference or production recommendation code is changed.

## What the numbers mean

`duration_profiles.yaml` contains author estimates, not measured results. Each
activity profile references its exact ID and content version and records a base
estimate for every supported age band. Base minutes include that activity's setup,
core steps and ending. Optional extension minutes refer to an existing entry in
`adaptations.extend`, with a limit of at most two extra rounds. They are never
inferred from the number of steps and never instruct a child to continue until
a timer expires. A family can pause or finish at any point.

Shared preparation, between-activity rest and transitions are separate blocks.
These are flexible planning allowances, not required exercise or rest prescriptions.

| Combo budget | Activities | Shared preparation | Rest between each pair | Transition between each pair |
| --- | ---: | ---: | ---: | ---: |
| 20 minutes | 2 | 2 | 2 | 1 |
| 40 minutes | 3 | 3 | 3 | 1 |
| 60 minutes | 3 | 3 | 4 | 2 |

The preview accepts explicitly chosen IDs in the caller's order. It does not
select or rank activities. It schedules the complete core activity first, then
adds optional authored extensions in rounds while there is room. This simple
order-dependent allocation does not promise the mathematically closest fit.
Original steps and endings remain in the referenced activity records.

## Development preview

Install `content/requirements.txt` as described in the activity integration guide.
From the repository root:

```text
python content/tools/plan_combo_preview.py --duration 20 --age-band 5-7 --activity-id rhythm_steps --activity-id colour_hunt
python content/tools/plan_combo_preview.py --duration 40 --age-band 8-10 --activity-id follow_the_leader --activity-id colour_hunt --activity-id pass_and_move --output content/examples/combo.preview.json
python content/tools/plan_combo_preview.py --duration 60 --age-band 8-10 --activity-id follow_the_leader --activity-id colour_hunt --activity-id pass_and_move
```

Output is always `mode: development_preview` and
`timing_basis: author_estimate_not_measured`, even if activities are later reviewed.
The committed combo example is a separate data shape from the existing backend
Combo response. Resolve each activity block's ID, version and age against the
activity library to obtain equipment, requirements, setup, steps and ending.
Do not treat an activity review as approval of its timing estimate.

| Status | Meaning | Consumer action |
| --- | --- | --- |
| `fits_estimate` | Planned blocks sum to the requested budget | Show as an estimate, not a verified schedule |
| `unused_time` | Core activities and permitted extensions leave time unused | Display `unused_minutes`; invite another choice or a shorter outing |
| `over_budget` | Even the core plan exceeds the budget | Reject this combination or choose a longer budget; do not truncate steps |

Unused time is not silently labelled as free play or rest. In the supplied
40-minute example, 38 minutes are scheduled and 2 remain unused. The same IDs
and age at 60 minutes schedule 48 minutes and leave 12 unused. This exposes a
content-duration gap rather than claiming that three short games fill an hour.
Unknown IDs, missing ages, duplicate IDs and wrong activity counts raise errors.

## Before using timing in a live recommendation

Try each proposed activity and record its ID, version, age band, actual setup/core
time, any extension used and interruptions. Do not record identifying child data.
Distinguish an adult walkthrough from an outing with a child. Review estimates
using that evidence; do not increase them merely to remove unused time.
Evidence collection, a reviewed timing contract and production integration remain
future work. This module intentionally cannot publish timing as approved.

The configuration validator rejects missing or duplicate profiles, unknown IDs,
content-version mismatches, missing age estimates and invalid extension references.
Update timing profiles when the activity version or supported age bands change.

## Coverage report

```text
python content/tools/report_activity_coverage.py --output content/activities/COVERAGE.md
```

The report separates draft and reviewed content and lists type-level subtype
shortlists. It does not certify that any particular place supports an activity.
Racket and wheeled content remain deferred; no generic fallback is inserted for
skate parks or BMX tracks.
