# Migrated mission review queue

Author: Jiabin. All 18 families remain draft and all review cells are pending.
Review the migrated YAML, not only the original activity idea. Nothing below is
an assertion that an adult walkthrough, child test or timing measurement happened.

## Review order

Start with Colour Hunt and Follow the Leader, then the other four pilot ideas:
Balance Shapes, Imaginary Delivery, Notice the Change and Pass and Move.
Continue with the remaining twelve after those demonstrate the full handoff.

| Template ID | 5-7 prefixes 3/5/7 | 8-10 prefixes 3/5/7 | 11-12 prefixes 3/5/7 | Reviewer | Decision / notes |
| --- | --- | --- | --- | --- | --- |
| activity_balance_shapes | Pending | Pending | Pending | Unassigned | Pending |
| activity_choose_your_route | Pending | Pending | Pending | Unassigned | Pending |
| activity_colour_hunt | Pending | Pending | Pending | Unassigned | Pending |
| activity_follow_the_leader | Pending | Pending | Pending | Unassigned | Pending |
| activity_imaginary_delivery | Pending | Pending | Pending | Unassigned | Pending |
| activity_invisible_orchestra | Pending | Pending | Pending | Unassigned | Pending |
| activity_listen_and_point | Pending | Pending | Pending | Unassigned | Pending |
| activity_notice_the_change | Pending | Pending | Pending | Unassigned | Pending |
| activity_opposite_actions | Pending | Pending | Pending | Unassigned | Pending |
| activity_partner_ball_carry | Pending | Pending | Pending | Unassigned | Pending |
| activity_pass_and_move | Pending | Pending | Pending | Unassigned | Pending |
| activity_rhythm_steps | Pending | Pending | Pending | Unassigned | Pending |
| activity_robot_instructions | Pending | Pending | Pending | Unassigned | Pending |
| activity_roll_to_target | Pending | Pending | Pending | Unassigned | Pending |
| activity_silent_scene | Pending | Pending | Pending | Unassigned | Pending |
| activity_sort_and_step | Pending | Pending | Pending | Unassigned | Pending |
| activity_step_and_pause | Pending | Pending | Pending | Unassigned | Pending |
| activity_viewpoint_switch | Pending | Pending | Pending | Unassigned | Pending |

## Check each band and each stopping point

- Read the parent's briefing and every step aloud; check that supervision, permitted
  space, equipment and stopping choices are understandable before play.
- Try steps 1-3 alone, 1-5 alone and 1-7. Each prefix must work without later steps.
- Check that every step is a real task, not a greeting, praise or padding.
- Compare bands for actual difficulty differences; do not approve vocabulary-only changes.
- Check every instruction against all nine safety rules and against actual site requirements.
- Inspect any facility warning rather than assuming category labels prove equipment exists.
- Review Sort and Step's spoken grouping and Roll to Target's adult-hand target as changed games.
- Keep self confirmation until Backend B supplies measured kept prompts matching a step's task.
- Record observed duration separately; 20/40/60 labels currently come from step counts only.
- Distinguish an adult walkthrough from a child outing, and do not collect identifying child data.

Record Pass, Needs changes or Not suitable for each tested band/prefix in the table
or linked review notes. One failed prefix means revise before approving the family.
Do not shorten a band without updating its longest bucket and dependent tests.

## Promotion

The reviewer must be a real team member other than Jiabin. After they actually
approve the family, fill `review.reviewed_by`, set `review.status: reviewed`, and
move the single YAML into `missions/reviewed/` with the same filename. Keep no
second copy. Do not promote the original `activities/` representation as well.
If reviewed content changes later, return it to draft and re-review; record the
change in its Git commit/PR because Priyan's family contract has no version field.

Regenerate both mission preview exports and run the commands in
[MIGRATION.md](MIGRATION.md). Reviewed output stays empty until promotion.
Before deployment, also verify parent briefing display, source and generated
Mission validation, context handling, photo/manual failure paths and offline use.
The consolidated AI usage statement remains a final team handoff task.
