# Reviewing mission templates

Read this once. It takes five minutes. Then you can review.

---

## What we are building

The app tells a family **where** to go. A mission tells them **what to do** when they
get there. A mission is five or seven short instructions the parent reads aloud, one at
a time, while the child goes and does them. The child never holds the phone.

We are not writing missions one by one. We write **templates**, and a model rewrites the
wording for today's park and today's weather. So a template has to be good, because it
gets used hundreds of times.

## Why we need you

We need about **48 templates**. Drafting them is fast — a model writes three in a couple
of minutes. Reading them is the slow part, and it cannot be skipped, because a template
tells a real child what to do in a real park.

**Your job is to read drafts and decide: ship it, fix it, or bin it.**

About 5 minutes per template. You have been given a set below.

---

## What a template looks like

One template covers three age groups. Same idea, three difficulty levels.

```yaml
template_id: speed_challenge
title: Speed challenge
category: cycling_track
duration_bucket: 60          # 7 steps
mechanic: move
bands:
  5-7:
    steps:
      - "Ride to a tree you can see and stop."
      - "Turn around and ride back to where you started."
      ...
  8-10:
    steps:
      - "Ride to a tree, then back, counting your pedal pushes."
      ...
  11-12:
    steps:
      - "Ride there and back twice, then try to beat your own count."
      ...
```

Two things to notice.

**Steps get shorter, not different.** A 60-minute mission has 7 steps. The 40-minute
version is the first 5. The 20-minute version is the first 3. So each step has to work
as an ending — no step can depend on a later one.

**The three bands are difficulty, not vocabulary.** If the only difference between 5-7
and 11-12 is that "stop" became "halt", that is a fail. The task itself must get harder.

---

## How to review one

Read every step out loud. Seriously — say it. Most problems only appear when you hear it.

Then check these seven things.

### 1. Could a child do this after hearing it once?

If they would have to ask "wait, what?", it fails. No step should need repeating or
explaining.

### 2. Is it safe?

Nine rules, in `schema/safety_constraints.yaml`. No climbing above knee height, no going
into water, no leaving the adult's sight, no crossing roads, no approaching animals or
strangers, no picking up litter or unknown objects, no tasting anything, no digging, no
tunnels or dense scrub.

The checker catches obvious phrasings. **It cannot catch a step that is unsafe in a way
nobody wrote a rule for.** That is why a human reads it.

### 3. Does it invent things that might not be there?

We know a place's category and nothing else. We do not know it has cones, flags, painted
lines, benches, signs or equipment.

- Bad: "Ride to the orange cone."
- Good: "Pick a tree you can see and ride to it."

Let the child choose the landmark.

### 4. Is every step an actual activity?

No waving, no cheering, no "well done", no "tell an adult you had fun". Those are padding
to reach seven steps. If a family cannot fill seven real steps, it is a weak idea.

### 5. Do the three bands really differ?

Look at step 1 in all three bands side by side. If they are the same instruction in
different words, mark it for a fix.

### 6. Is the 5-7 wording short enough?

Under 12 words per step. The checker enforces this, but if a step is technically 11 words
and still confusing for a six-year-old, flag it.

### 7. Would a child want to do this twice?

The one thing no script can check. Trust your gut. A boring template is a failed
template, because our whole point is that the child asks to go again.

---

## The three outcomes

**Ship it** — set `reviewed_by:` to your name and `status: reviewed`. Move it from
`missions/_candidates/` into `missions/<category>.yaml`.

**Fix it** — edit the wording yourself, then ship it. Small fixes are faster than sending
it back.

**Bin it** — delete it. Say why in the pull request. Three good templates beat four with
a dud, and we can always draft more.

---

## Running the checker

Before and after you edit:

```
cd content
python schema/check_drafts.py
```

**Errors** must be zero before you commit. **Warnings** are fine for now — most of them
say "prompt not yet measured" or "not shippable", which is true until we finish the
photo prompt measurement.

The checker catches step counts, banned phrases, filler, invented features, duplicated
ideas and truncated drafts. It does **not** catch boring, confusing, or subtly unsafe.
That is what you are for.

---

## One rule that is not negotiable

**Nobody reviews their own drafts.** If you ran the batch, someone else reads it. This is
in the definition of done for a reason — a safety artefact checked only by the person who
made it has not been checked.

---

## Allocation

| Who | Categories | Families to review |
| --- | --- | --- |
| A | park_and_garden, playground | ~12 |
| B | sports_ground, walking_track | ~12 |
| C | cycling_track, reserve_and_bushland | ~12 |
| D | waterway_and_foreshore, bare_site | ~12 |

Review someone else's categories, not the ones you drafted. Swap if that clashes.

**Time:** roughly one hour each, in fifteen-minute chunks. Do not do all twelve in one
sitting — you stop noticing problems around number six.

## Order of work

1. Run `python tools/coverage.py --target 6` to see what is missing
2. Someone drafts a batch of three into `missions/_candidates/`
3. Run the checker, fix the errors
4. Someone else reviews the three against the seven questions above
5. Promote the good ones, delete the rest
6. Commit, and repeat

## Questions still open

Two things affect what you review, so raise them rather than guessing:

- The seven category codes are placeholders. They will be swapped for the real ones from
  the data pipeline. Do not write anything that depends on a category name.
- Photo steps are all disabled until the prompt measurement runs. Everything is
  tap-to-confirm for now. If a step would be better with a photo, note it and move on.