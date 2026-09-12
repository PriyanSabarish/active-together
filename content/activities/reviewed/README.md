# Reviewed activities

There are no approved activities here yet.

After another team member reviews every age variant, record that person's name,
set `review.status: reviewed`, and move the activity YAML from `_candidates/` here.
Changes to reviewed content require a version increment and another review;
move it back to `_candidates/` with draft status and a null reviewer while editing.

`load_reviewed_activities()` reads only the YAML files in this directory and
checks each record's schema and review status. Matching author/reviewer names
are rejected; the team must verify that independent human review actually took
place. An invalid record raises an error rather than falling back to drafts.
An empty reviewed directory returns an empty list. The application has not yet
been connected to this loader.
