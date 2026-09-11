# Reviewed activities

There are no approved activities here yet.

After another team member reviews every age variant, record that person's name,
set `review.status: reviewed`, and move the activity YAML from `_candidates/` here.
Changes to reviewed content require a version increment and another review;
move it back to `_candidates/` with draft status and a null reviewer while editing.

The future runtime loader will read only `reviewed/*.yaml`, validate each file,
and check reviewer identity and status. Do not load candidates or use an invalid
reviewed record as a fallback. Module 1 defines this rule; it does not implement
the runtime loader.
