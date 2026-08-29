# Backend B — recommendation logic

Owns deciding what to do with the data Backend A provides: duration bucketing,
environmental tiering, eligibility, ordering and explanation construction.

Does **not** query the database or call external APIs. Everything arrives as a
function argument, which is why every task here can be developed against
fixtures before any infrastructure exists.

## Responsibilities

| Area | Detail |
|---|---|
| Duration | Bucketing 20–120 minutes into 20/40/60, with the tie-break rule |
| Environment | Threshold configuration, tier assignment, warnings and reminders |
| Eligibility | Which candidates can be recommended at all |
| Ordering | Deterministic sort — tier, then distance, then name |
| Output | Combo payloads, explanations, zero-result responses |

## What Backend B provides

```python
recommend(candidates, context, duration_min) -> Recommendation
```

Consumed by Backend A's endpoint layer (task A12). Takes a list of `Place`, a
`Context`, and the parent's entered duration. Returns a `Recommendation`
containing at most three `Combo` objects, or a zero-result status with a
message.

## Thresholds

From acceptance criteria 2.2 and 2.3. **All thresholds are inclusive.**

| Condition | Threshold | Effect |
|---|---|---|
| Precipitation probability | ≥ 0.60 | Warning + deprioritised |
| Wind gusts | ≥ 40.0 km/h | Warning + deprioritised |
| PM2.5 | ≥ 25.0 µg/m³ | Warning + deprioritised |
| PM10 | ≥ 80.0 µg/m³ | Warning + deprioritised |
| UV index | ≥ 3.0 | Reminder only — **not** deprioritised |

UV is the exception. Story 2.3 requires a sun-protection reminder without
removing the candidate or making a safety claim based on UV alone.

These live in a configuration file, not as inline constants. They will be tuned
repeatedly during scenario testing and must be inspectable for the report.

## Duration bucketing

Entered duration is 20–120 minutes, matched to the nearest 20, 40 or 60 minute
bucket. **An exact tie selects the lower bucket.**

| Entered | Bucket |
|---|---|
| 20 | 20 |
| 30 | 20 — tie, lower wins |
| 45 | 40 |
| 50 | 40 — tie, lower wins |
| 120 | 60 |

Both the entered duration and the matched bucket are shown to the parent, with
the duration labelled as excluding transport and travel time.

## Ordering

Story 3.1, in order:

1. Normal tier before deprioritised tier
2. Within a tier, by `distance_m` ascending
3. Ties broken by place name

Maximum three combos. Fewer than three returns what exists — no padding.

## Explanations

Story 3.3. The explanation references **only** values actually used in the
decision: approximate distance, selected forecast time, entered duration,
matched bucket, and available environmental data.

It must not invent facilities, opening hours, cost or safety claims. Where a
supporting value is unavailable, it is labelled as unavailable or omitted —
never estimated.

## Testing without infrastructure

`tests/fixtures.py` provides hand-written `Place` and `Context` data.

### Place sets

| Name | Contents | Exercises |
|---|---|---|
| `DENSE_INNER` | 10 places, inner Melbourne, all 7 categories | Normal ranking |
| `MIDDLE_MONASH` | 4 places, Monash | Moderate density |
| `SPARSE_OUTER` | 2 places, Melton | Fewer-than-three path |
| `EMPTY` | none | Zero-result path |
| `LOW_CONFIDENCE` | 2 below any sensible threshold | Suppression |
| `SINGLE_CATEGORY` | derived from `DENSE_INNER` | Preference filtering (iteration 2) |

Two places have `display_name=None` deliberately — `fx_006` and `fx_102`.

### Boundary fixtures

Exist in pairs so the comparison operator can be verified:

- `RAIN_AT_THRESHOLD` is exactly 0.60 — must deprioritise
- `RAIN_BELOW_THRESHOLD` is 0.59 — must not
- `WIND_AT_THRESHOLD` is exactly 40.0 — must deprioritise

`UNAVAILABLE` covers a failed forecast call. `PARTIAL` covers a response where
some fields are present and some missing, which real APIs do.

### Scenarios

```python
from tests.fixtures import get_scenario

s = get_scenario("dense_clear")
s["places"], s["context"], s["duration_min"], s["expect"]
```

Nineteen scenarios including the duration ties at 30 and 50.

## Tasks

### Independent — start immediately

| ID | Task | Depends on |
|---|---|---|
| B1 | Fixture data set | Seam agreed |
| B2 | Duration bucketing with the 30/50 tie-break | Seam agreed |
| B3 | Environmental threshold configuration | Seam agreed |
| B4 | Tier assignment | B1, B3 |
| B5 | Eligibility filter | B1, B2 |

### Ranking and output

| ID | Task | Depends on |
|---|---|---|
| B6 | `recommend()` — deterministic ordering, maximum three | B4, B5 |
| B7 | Combo card payload | B6 |
| B8 | Explanation construction from verified inputs | B6 |
| B9 | Anti-invention rules | B8 |
| B10 | Zero-result response with suggested next actions | B5, B6 |
| B11 | Fewer-than-three handling | B6 |

### Validation and documentation

| ID | Task | Depends on |
|---|---|---|
| B12 | Validation methodology for classification accuracy | Nothing |
| B13 | Threshold review against scenario results | B4, scenario run |
| B14 | Document ranking configuration for the report | B6, B13 |

B12 is a design task with no dependencies. Writing it first lets the Data strand
execute the accuracy study without waiting.

### Forward spikes — after B6 only

| ID | Task | Question |
|---|---|---|
| B15 | Mission template schema plus two seed templates | What fields does a template need before bulk authoring? |
| B16 | Prompt vocabulary test — 20 candidates against real photos | Which prompts separate reliably enough for story 7.3? |
| B17 | In-browser pose estimation on a mid-range Android | Is Epic 10.3 viable as specified? |

## Suggested order

```
B1 → B2 → B3 → B4 → B5 → B6 → B11 → B10 → B7 → B8 → B9 → B13 → B14
```

B12 at any point. B15–B17 only after B6 and only if capacity allows.

## Needs from others

| Needs | From | Blocks |
|---|---|---|
| Seam signatures agreed | Backend A | Everything — the only hard blocker |
| Category counts per LGA | Data | Realistic B10 testing |
| Base combo templates for the three buckets | **Unassigned** | B5 eligibility, B7 payload |
| Live `Context` objects | Backend A | Only B13 tuning — fixtures cover the rest |

## Open questions

- **Base combo templates** — story 3.1 makes "a base combo exists for the
  matched bucket" an eligibility condition, and story 3.2 requires displaying
  it. Seven categories across three buckets is 21 combinations minimum. This
  work has no owner.
- **Confidence threshold** — applied in Backend A's query, in `B5` eligibility,
  or already by the pipeline?
- **Category counts per LGA** — determines whether the zero-result path is a
  common case or an edge case.
