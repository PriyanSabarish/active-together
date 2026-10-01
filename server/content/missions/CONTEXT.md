# Context preparation for future selection

These content-side hooks do not change `select_templates`, `/missions`, `/verify-step`
or the current server Context model. Backend B adapts its real data into the
normalized fixture inputs below. No model, network call, API credential or user
address is needed by the template loader.

| Input | Content preparation | Backend responsibility |
| --- | --- | --- |
| Address and coordinates | None in family files | Resolve address and select nearby places upstream; do not copy addresses into templates or generation prompts |
| Place | `category`, `site_requirements`, binding shortlist | Exact category/subtype mapping and evidence for required capabilities |
| Weather | `weather_tags` | Evaluate conditions at the chosen place and outing time under shared rules |
| Air quality | No duplicated numeric thresholds | Evaluate existing environment policy with pollutant units, observation/forecast time and availability |
| Preferences | Stable content types and a separate `preference_codes` binding | Supply the real frontend vocabulary, exclusion/relaxation and ranking policy |
| Age and duration | Three bands and the authored longest bucket | Hard age selection and B29 prefix construction; never substitute a different age |
| Recent history | Stable migration template ID and source activity ID | Pass recent IDs and apply repetition policy, outside template storage |

## Known and unknown conditions

`category: any` means the family is not tied to one category. It does not mean
every site supports it. The bindings use the dataset's seven actual category
codes, not the older placeholder mission categories. They are coarse candidate
shortlists; subtype suitability and access still need checking. There is no
automatic skate/BMX fallback. No claim of 21 ready base combos is made.

`bare_site` is an adult-checked permitted starting area, not an assumed grass lawn
or fence. `open_space` means enough clear, level room for the particular task,
away from traffic, other users and equipment travel/landing areas. The source
place dataset does not establish either capability by itself. These conservative
definitions must be reconciled with Backend B's actual feature evidence before use.
Unknown evidence remains unknown; a category, a confidence score or a non-empty
string is not positive proof of a usable feature.

Dry tags on movement and ball families are conservative draft restrictions, not
field-tested weather suitability. `any` on observation or stationary imagination
only means no specific weather dependency; global weather and air-quality gates
still apply. This batch does not claim explicit wet, windy or hot-weather coverage.
Missing, stale or mismatched-location/time environmental data must not be converted
to a positive gate. The backend owns that evaluation; no AQI cutoff is invented here.

## Demonstration helper, not a replacement selector

`assess_conditions` uses normalized synthetic or evidence-backed values:

```python
place = {
    "activity_category": "park_and_garden",
    "confirmed_features": {"bare_site": True, "open_space": True},
}
context = {
    "weather_allowed": True,
    "air_quality_allowed": True,
    "weather_tags": ["dry"],
}
```

The booleans above are a positive test fixture, not assertions about a real park.
Use `None` or omit a key when evidence is unavailable. `False` means an explicit
exclusion. The helper returns `candidate`, `needs_context` or `excluded` with
reasons. Candidate is not reviewed status, approval, a timed recommendation or
permission to send a child somewhere. Equipment availability, age selection,
access, ranking, recency and all runtime safety checks remain caller responsibilities.

The actual frontend preference codes were not found in this checkout. Every
binding therefore has `preference_codes: []` and the file is `unbound`. Empty codes
are not a claim that the family ignores preferences. When non-empty user preferences
arrive before binding, the helper reports `preference_codes_unbound` rather than
silently disregarding them. Backend B/Client must supply their agreed vocabulary;
then populate these lists and mark the binding file `bound` together.

Normalized preferences use lists named `excluded_codes` and `preferred_codes`.
These are adapter fixture names, not a change to the public API. Exclusions are
reported separately; positive preferences produce only a `preference_match` hint,
not a ranking score. If all options are excluded, Backend B applies its existing
relaxation policy and explains it to the parent. Relaxing preferences must never
override age, missing/unsafe site evidence or environmental restrictions.

## Tests and outstanding integration work

Fixtures cover missing and negative site evidence, unknown weather/air quality,
any-weather families still needing environment checks, adverse weather, excluded
categories, unbound preferences and preference exclusion. Age/bucket rejection
and reviewed-empty behavior are tested in the mission suite.

Before deployment, Backend B/Client must bind real preference codes, map actual
environment outputs and capability evidence, exercise absent/stale context and
recent-history behavior, and choose the defined no-candidate response. These are
explicit receiving-system tasks, not unfinished template field definitions.
