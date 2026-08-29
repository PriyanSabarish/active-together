"""
Fixture data for Backend B (task B1).

recommendation logic be built and tested without PostGIS, without
Open-Meteo, and without Backend A existing yet.

Scenarios covered:
  PLACES   dense inner, sparse outer, empty, unnamed, low-confidence,
           single-category (to exercise preference filtering later)
  CONTEXT  clear, rain, wind, high UV, poor air, multiple warnings, unavailable
"""

from app.models import ActivityCategory, Context, Place


#  PLACES


# Dense inner-Melbourne set. Search origin assumed near Carlton
# (-37.8010, 144.9660). Distances are approximate straight-line.
DENSE_INNER: tuple[Place, ...] = (
    Place(
        place_id="fx_001",
        display_name="Argyle Square",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.8021, longitude=144.9662,
        distance_m=130,
        classification_confidence=0.94,
    ),
    Place(
        place_id="fx_002",
        display_name="Lincoln Square Playground",
        activity_category=ActivityCategory.PLAYGROUND,
        lga_name="Melbourne",
        latitude=-37.8035, longitude=144.9640,
        distance_m=310,
        classification_confidence=0.97,
    ),
    Place(
        place_id="fx_003",
        display_name="Carlton Gardens",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.8055, longitude=144.9711,
        distance_m=640,
        classification_confidence=0.96,
    ),
    Place(
        place_id="fx_004",
        display_name="Princes Park Oval",
        activity_category=ActivityCategory.SPORTS_GROUND,
        lga_name="Melbourne",
        latitude=-37.7847, longitude=144.9622,
        distance_m=1850,
        classification_confidence=0.91,
    ),
    Place(
        place_id="fx_005",
        display_name="Curtain Square Tennis Courts",
        activity_category=ActivityCategory.COURT,
        lga_name="Melbourne",
        latitude=-37.7856, longitude=144.9713,
        distance_m=1790,
        classification_confidence=0.88,
    ),
    Place(
        place_id="fx_006",
        display_name=None,                      
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.7990, longitude=144.9701,
        distance_m=390,
        classification_confidence=0.72,
    ),
    Place(
        place_id="fx_007",
        display_name="Royal Park Picnic Area",
        activity_category=ActivityCategory.PICNIC_DAY_USE,
        lga_name="Melbourne",
        latitude=-37.7885, longitude=144.9520,
        distance_m=1960,
        classification_confidence=0.85,
    ),
    Place(
        place_id="fx_008",
        display_name="Riverslide Skate Park",
        activity_category=ActivityCategory.SKATE_BMX,
        lga_name="Melbourne",
        latitude=-37.8228, longitude=144.9789,
        distance_m=2560,
        classification_confidence=0.93,
    ),
    Place(
        place_id="fx_009",
        display_name="Capital City Trail Access",
        activity_category=ActivityCategory.TRAIL_ACCESS,
        lga_name="Melbourne",
        latitude=-37.7940, longitude=144.9580,
        distance_m=1080,
        classification_confidence=0.79,
    ),
    Place(
        place_id="fx_010",
        display_name="Flagstaff Gardens",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.8112, longitude=144.9550,
        distance_m=1500,
        classification_confidence=0.95,
    ),
)


# Sparse outer set — Melton. Two candidates, both distant.
SPARSE_OUTER: tuple[Place, ...] = (
    Place(
        place_id="fx_101",
        display_name="Melton Reserve",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melton",
        latitude=-37.6841, longitude=144.5852,
        distance_m=2400,
        classification_confidence=0.83,
    ),
    Place(
        place_id="fx_102",
        display_name=None,
        activity_category=ActivityCategory.SPORTS_GROUND,
        lga_name="Melton",
        latitude=-37.6902, longitude=144.5710,
        distance_m=4100,
        classification_confidence=0.68,
    ),
)


# Middle-ring set — Monash. Moderate density, mixed categories.
MIDDLE_MONASH: tuple[Place, ...] = (
    Place(
        place_id="fx_201",
        display_name="Clayton Reserve Playground",
        activity_category=ActivityCategory.PLAYGROUND,
        lga_name="Monash",
        latitude=-37.9160, longitude=145.1210,
        distance_m=820,
        classification_confidence=0.92,
    ),
    Place(
        place_id="fx_202",
        display_name="Napier Park",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Monash",
        latitude=-37.9088, longitude=145.1340,
        distance_m=1240,
        classification_confidence=0.90,
    ),
    Place(
        place_id="fx_203",
        display_name="Monash Sports Ground",
        activity_category=ActivityCategory.SPORTS_GROUND,
        lga_name="Monash",
        latitude=-37.9215, longitude=145.1395,
        distance_m=1970,
        classification_confidence=0.87,
    ),
    Place(
        place_id="fx_204",
        display_name="Bogong Reserve Picnic Area",
        activity_category=ActivityCategory.PICNIC_DAY_USE,
        lga_name="Monash",
        latitude=-37.9050, longitude=145.1180,
        distance_m=1610,
        classification_confidence=0.81,
    ),
)


# No candidates at all — exercises the zero-result path 
EMPTY: tuple[Place, ...] = ()


# All one category — useful later for preference filtering 
SINGLE_CATEGORY: tuple[Place, ...] = tuple(
    p for p in DENSE_INNER
    if p.activity_category == ActivityCategory.PARK_AND_GARDEN
)


# Below any sensible confidence threshold — exercises suppression 
LOW_CONFIDENCE: tuple[Place, ...] = (
    Place(
        place_id="fx_301",
        display_name=None,
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.8005, longitude=144.9688,
        distance_m=250,
        classification_confidence=0.31,
    ),
    Place(
        place_id="fx_302",
        display_name="Unnamed Reserve",
        activity_category=ActivityCategory.SPORTS_GROUND,
        lga_name="Melbourne",
        latitude=-37.7995, longitude=144.9645,
        distance_m=420,
        classification_confidence=0.44,
    ),
)



# CONTEXT
# Threshold reference (stories 2.2, 2.3):
#   precip_prob    >= 0.60   -> warning + deprioritised
#   wind_gust_kmh  >= 40.0   -> warning + deprioritised
#   pm25           >= 25.0   -> warning + deprioritised
#   pm10           >= 80.0   -> warning + deprioritised
#   uv_index       >= 3.0    -> reminder only, NOT deprioritised

CLEAR_MILD = Context(
    available=True,
    temp_c=19.0, precip_prob=0.10, wind_gust_kmh=12.0,
    uv_index=2.0, pm25=6.0, pm10=14.0,
)

# UV at exactly the threshold — reminder, no deprioritisation
CLEAR_HIGH_UV = Context(
    available=True,
    temp_c=28.0, precip_prob=0.05, wind_gust_kmh=15.0,
    uv_index=3.0, pm25=8.0, pm10=18.0,
)

# Precipitation exactly at threshold — boundary case, should deprioritise
RAIN_AT_THRESHOLD = Context(
    available=True,
    temp_c=14.0, precip_prob=0.60, wind_gust_kmh=18.0,
    uv_index=1.0, pm25=7.0, pm10=15.0,
)

# Just below threshold — should NOT deprioritise
RAIN_BELOW_THRESHOLD = Context(
    available=True,
    temp_c=14.0, precip_prob=0.59, wind_gust_kmh=18.0,
    uv_index=1.0, pm25=7.0, pm10=15.0,
)

RAIN_HEAVY = Context(
    available=True,
    temp_c=12.0, precip_prob=0.85, wind_gust_kmh=22.0,
    uv_index=1.0, pm25=5.0, pm10=11.0,
)

# Wind exactly at threshold
WIND_AT_THRESHOLD = Context(
    available=True,
    temp_c=16.0, precip_prob=0.20, wind_gust_kmh=40.0,
    uv_index=3.0, pm25=9.0, pm10=20.0,
)

WIND_STRONG = Context(
    available=True,
    temp_c=15.0, precip_prob=0.25, wind_gust_kmh=58.0,
    uv_index=2.0, pm25=10.0, pm10=22.0,
)

# PM2.5 at threshold
POOR_AIR_PM25 = Context(
    available=True,
    temp_c=24.0, precip_prob=0.10, wind_gust_kmh=8.0,
    uv_index=5.0, pm25=25.0, pm10=48.0,
)

# PM10 at threshold, PM2.5 below — only PM10 triggers
POOR_AIR_PM10 = Context(
    available=True,
    temp_c=23.0, precip_prob=0.10, wind_gust_kmh=9.0,
    uv_index=4.0, pm25=18.0, pm10=80.0,
)

# Smoke haze — several thresholds crossed at once
POOR_AIR_SEVERE = Context(
    available=True,
    temp_c=31.0, precip_prob=0.05, wind_gust_kmh=6.0,
    uv_index=9.0, pm25=62.0, pm10=140.0,
)

# Multiple warnings — rain AND wind
STORMY = Context(
    available=True,
    temp_c=11.0, precip_prob=0.90, wind_gust_kmh=65.0,
    uv_index=1.0, pm25=4.0, pm10=9.0,
)

# Forecast call failed (story 2.2 unavailable path)
UNAVAILABLE = Context(available=False)

# Partial data — some fields present, some missing. Real APIs do this.
PARTIAL = Context(
    available=True,
    temp_c=17.0, precip_prob=0.30, wind_gust_kmh=None,
    uv_index=None, pm25=None, pm10=None,
)


# Named scenarios — pair a place set with a context


SCENARIOS: dict[str, dict] = {
    "dense_clear": {
        "places": DENSE_INNER, "context": CLEAR_MILD, "duration_min": 45,
        "expect": "Three normal-tier combos, ordered by distance.",
    },
    "dense_rain": {
        "places": DENSE_INNER, "context": RAIN_HEAVY, "duration_min": 45,
        "expect": "All outdoor candidates deprioritised and warned.",
    },
    "dense_boundary_rain": {
        "places": DENSE_INNER, "context": RAIN_AT_THRESHOLD, "duration_min": 45,
        "expect": "Deprioritised at exactly 0.60 — inclusive threshold.",
    },
    "dense_below_rain": {
        "places": DENSE_INNER, "context": RAIN_BELOW_THRESHOLD, "duration_min": 45,
        "expect": "Normal tier at 0.59 — confirms the boundary is inclusive.",
    },
    "dense_high_uv": {
        "places": DENSE_INNER, "context": CLEAR_HIGH_UV, "duration_min": 45,
        "expect": "Sun-protection reminder, tier stays normal.",
    },
    "dense_wind_boundary": {
        "places": DENSE_INNER, "context": WIND_AT_THRESHOLD, "duration_min": 45,
        "expect": "Deprioritised at exactly 40 km/h.",
    },
    "dense_poor_air": {
        "places": DENSE_INNER, "context": POOR_AIR_PM25, "duration_min": 45,
        "expect": "Air-quality warning, deprioritised, plus UV reminder.",
    },
    "dense_stormy": {
        "places": DENSE_INNER, "context": STORMY, "duration_min": 45,
        "expect": "Two warnings on one combo — rain and wind.",
    },
    "dense_no_weather": {
        "places": DENSE_INNER, "context": UNAVAILABLE, "duration_min": 45,
        "expect": "Candidates still shown, weather labelled unavailable.",
    },
    "dense_partial_weather": {
        "places": DENSE_INNER, "context": PARTIAL, "duration_min": 45,
        "expect": "Present fields shown, missing fields labelled unavailable.",
    },
    "sparse_clear": {
        "places": SPARSE_OUTER, "context": CLEAR_MILD, "duration_min": 45,
        "expect": "Two combos only — no padding to three.",
    },
    "sparse_rain": {
        "places": SPARSE_OUTER, "context": RAIN_HEAVY, "duration_min": 45,
        "expect": "Two deprioritised combos. Nothing normal-tier to rank above.",
    },
    "middle_clear": {
        "places": MIDDLE_MONASH, "context": CLEAR_MILD, "duration_min": 60,
        "expect": "Three combos, 60-minute bucket.",
    },
    "empty": {
        "places": EMPTY, "context": CLEAR_MILD, "duration_min": 45,
        "expect": "Zero-result status with suggested next actions.",
    },
    "low_confidence_only": {
        "places": LOW_CONFIDENCE, "context": CLEAR_MILD, "duration_min": 45,
        "expect": "Zero results if the threshold suppresses these.",
    },
    "duration_tie_30": {
        "places": DENSE_INNER, "context": CLEAR_MILD, "duration_min": 30,
        "expect": "Bucket 20, not 40 — tie selects the lower bucket.",
    },
    "duration_tie_50": {
        "places": DENSE_INNER, "context": CLEAR_MILD, "duration_min": 50,
        "expect": "Bucket 40, not 60 — tie selects the lower bucket.",
    },
    "duration_min": {
        "places": DENSE_INNER, "context": CLEAR_MILD, "duration_min": 20,
        "expect": "Bucket 20, lower bound accepted.",
    },
    "duration_max": {
        "places": DENSE_INNER, "context": CLEAR_MILD, "duration_min": 120,
        "expect": "Bucket 60, upper bound accepted.",
    },
}


def get_scenario(name: str) -> dict:
    """Fetch a named scenario, with a helpful error if the name is wrong."""
    if name not in SCENARIOS:
        raise KeyError(
            f"Unknown scenario '{name}'. Available: {', '.join(sorted(SCENARIOS))}"
        )
    return SCENARIOS[name]
