# Migrated mission review queue

Author: Jiabin. All eighteen migrated families are reviewed by lychen, as confirmed
by Jiabin. Review the migrated YAML, not only the original activity idea.
Separate band/prefix observations were not supplied with the
approval and have not been invented here. No adult walkthrough, child test or
timing measurement is claimed by this status update.

## Review status

Colour Hunt and Follow the Leader were approved first. Jiabin subsequently
confirmed lychen's review of the remaining sixteen families. All eighteen are
now in `missions/reviewed/`. Keep the checklist below for future revisions.

| Template ID | 5-7 prefixes 3/5/7 | 8-10 prefixes 3/5/7 | 11-12 prefixes 3/5/7 | Reviewer | Decision / notes |
| --- | --- | --- | --- | --- | --- |
| activity_balance_shapes | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_choose_your_route | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_colour_hunt | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_follow_the_leader | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_imaginary_delivery | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_invisible_orchestra | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_listen_and_point | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_notice_the_change | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_opposite_actions | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_partner_ball_carry | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_pass_and_move | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_rhythm_steps | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_robot_instructions | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_roll_to_target | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_silent_scene | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_sort_and_step | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_step_and_pause | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |
| activity_viewpoint_switch | Not separately recorded | Not separately recorded | Not separately recorded | lychen | Family reviewed; approval reported by Jiabin |

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

Regenerate the reviewed export and both mission preview exports using the commands
in [MIGRATION.md](MIGRATION.md). Reviewed output now contains all eighteen families.
Before deployment, also verify parent briefing display, source and generated
Mission validation, context handling, photo/manual failure paths and offline use.
The consolidated AI usage statement remains a final team handoff task.
