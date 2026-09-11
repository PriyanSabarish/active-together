# Pilot activity review

The pilot now contains six draft activities and eighteen age variants. Structure
checks and development export are ready. Independent human review and application
integration are still pending. Only reviewed content may enter the live activity
library. This checklist applies to activities/, not the older mission templates.

## Review queue

Review the YAML file with the matching activity ID under `_candidates/`. Record
the outcome for each age band before deciding whether to approve the whole file.

| Activity ID | Main difference from the other games | 5-7 | 8-10 | 11-12 | Reviewer | Decision / notes |
| --- | --- | --- | --- | --- | --- | --- |
| balance_shapes | Grounded balance and controlled transitions | Pending | Pending | Pending | Unassigned | Pending |
| colour_hunt | Find and compare visible colours | Pending | Pending | Pending | Unassigned | Pending |
| follow_the_leader | Copy and teach movement patterns | Pending | Pending | Pending | Unassigned | Pending |
| imaginary_delivery | Invent and adapt a pretend delivery | Pending | Pending | Pending | Unassigned | Pending |
| notice_the_change | Remember and compare small pose changes | Pending | Pending | Pending | Unassigned | Pending |
| pass_and_move | Roll a soft ball and adjust partner positions | Pending | Pending | Pending | Unassigned | Pending |

The first pilot covers movement_play (2), exploration_play (2), imaginative_play
(1) and ball_play (1). Five activities require no equipment; pass_and_move requires
a soft ball. Racket and wheeled activities are deferred. These counts describe
content variety, not verified location coverage. All six files have author Jiabin.

## Read and try each age variant

Use Pass, Needs changes or Not suitable for each band. A different team member
from the author should perform the review and record their own name.

- Read setup, each instruction and the parent prompt aloud. Can a parent explain it easily?
- Try the sequence with another adult. Does every step follow naturally and have a clear ending?
- Compare the three bands. Does the task change in difficulty rather than only wording?
- Check participation, equipment and requirements against every step and adaptation.
- Check all steps against `../schema/safety_constraints.yaml` and the activity's own constraints.
- Check that no step depends on an unverified facility, supplied equipment or finding a specific object.
- Check that the activity can be paused or simplified and involves no performance ranking.
- Check that the core game is distinct and could stand alone or join a later story.

An adult walkthrough is not a child usability test. Record what was actually
tried, where wording was unclear and any further testing needed; do not claim
child testing or developmental validation unless it happened.

Useful focus points: Notice the Change must keep the child in the adult's sight;
Balance Shapes keeps both feet grounded; Imaginary Delivery uses no real parcels
or obstacles; Pass and Move pauses movement before repositioning or retrieving a ball.

## Approve, revise or defer

For an approved activity, enter the human reviewer in `review.reviewed_by`, set
`review.status: reviewed`, and move the YAML into `reviewed/`. Keep only one copy
of its activity ID. If one band is not ready, revise it or omit that band and review
the remaining complete record. Never substitute another age at runtime.
If pilot age coverage is deliberately reduced, update the documented counts and
the pilot-count expectations in `../tests/test_activity_library.py` accordingly.

If changes are needed, keep the file in `_candidates/` with draft status and a null
reviewer. Record the requested changes in this table or the pull request. A later
change to approved content increments its version and returns it to draft review.

After review, run from the repository root:

```text
python content/tools/validate_activity_templates.py --preview
python content/tools/validate_activity_templates.py
python content/tools/export_activity_templates.py --preview --output content/examples/activities.preview.json
python -m unittest discover -s content/tests -v
```

For production integration, run the exporter without `--preview`. An empty result
means no activity has been approved yet. Do not fill it with draft content.

## Deployment handoff

- [ ] Human review outcomes recorded for every activity selected for deployment.
- [ ] Reviewed-mode loading and exact age selection exercised by the receiving teammate.
- [ ] Required equipment, setup, steps, parent guidance and ending displayed correctly.
- [ ] Unavailable age, empty library and malformed-content error states checked.
- [ ] The four-step 11-12 Imaginary Delivery variant is displayed completely.
- [ ] Development preview data is excluded from the production content path.
- [ ] Consolidated AI usage statement added before final handoff.

This queue is intentionally unapproved. No reviewer, walkthrough or deployment
result has been filled in on the team's behalf. Timing and recommendation rules
remain later work; a validated activity library alone is not a complete deployment.
