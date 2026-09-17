"""
Fixture data for Backend B (task B19).

Lets template selection, validators, build_mission and generation be built
and tested with no content library, no inference service, and no
generator running.

Coverage:
  TEMPLATES  every age band (5-7, 8-10, 11-12), every duration bucket
             (20, 40, 60), both verify modes (photo, self), the "any"
             bare-site category, non-empty equipment, multiple weather
             tags on one template, and one full three-band family for
             build_mission truncation testing.
  MISSIONS   final wire-shape Mission objects — one per bucket/band pair —
             covering both verify modes among their steps.

All ids are synthetic ("fx_..." / "fxm_...") so they're never mistaken for
reviewed content under content/missions/.
"""

from app.missions.models import Band, MissionTemplate, Review, TemplateStep
from app.models import AgeBand, Mission, Step, VerifyMode


#  TEMPLATES


# Shortest bucket, youngest band, self-only steps.
BUCKET20_BAND_5_7_SELF = MissionTemplate(
    template_id="fx_bucket20_band5_7_self",
    title="Animal moves",
    category="playground",
    duration_bucket=20,
    weather_tags=["any"],
    site_requirements=["grass"],
    equipment=[],
    mechanic="move",
    bands={
        AgeBand.BAND_5_7: Band(
            title=None,
            steps=[
                TemplateStep(sequence=1, prompt_text="Hop like a frog to the fence.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=2, prompt_text="Crawl like a crab back again.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=3, prompt_text="Wave both arms like a bird.", verify_mode="self", prompt_id=None, variable=True),
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="draft"),
)

# Same bucket/band, but exercises the photo verify mode and prompt_id.
BUCKET20_BAND_5_7_PHOTO = MissionTemplate(
    template_id="fx_bucket20_band5_7_photo",
    title="Garden colours",
    category="park_and_garden",
    duration_bucket=20,
    weather_tags=["dry"],
    site_requirements=["grass", "trees"],
    equipment=[],
    mechanic="find",
    bands={
        AgeBand.BAND_5_7: Band(
            title=None,
            steps=[
                TemplateStep(sequence=1, prompt_text="Find something green.", verify_mode="photo", prompt_id="p_green", variable=True),
                TemplateStep(sequence=2, prompt_text="Find something red.", verify_mode="photo", prompt_id="p_red", variable=True),
                TemplateStep(sequence=3, prompt_text="Smell a flower.", verify_mode="self", prompt_id=None, variable=True),
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="draft"),
)

# Middle bucket/band, mixed verify modes.
BUCKET40_BAND_8_10 = MissionTemplate(
    template_id="fx_bucket40_band8_10",
    title="Equipment challenge",
    category="sports_ground",
    duration_bucket=40,
    weather_tags=["dry", "windy"],
    site_requirements=["play_equipment", "grass"],
    equipment=[],
    mechanic="count",
    bands={
        AgeBand.BAND_8_10: Band(
            title=None,
            steps=[
                TemplateStep(sequence=1, prompt_text="Find the tallest goal post.", verify_mode="photo", prompt_id="p_goal_post", variable=True),
                TemplateStep(sequence=2, prompt_text="Count how many lines are on the field.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=3, prompt_text="Find something blue.", verify_mode="photo", prompt_id="p_blue", variable=True),
                TemplateStep(sequence=4, prompt_text="Do ten star jumps on the grass.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=5, prompt_text="Show me your favourite spot and say why.", verify_mode="self", prompt_id=None, variable=True),
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="draft"),
)

# Longest bucket, oldest band.
BUCKET60_BAND_11_12 = MissionTemplate(
    template_id="fx_bucket60_band11_12",
    title="Trail explorer",
    category="walking_track",
    duration_bucket=60,
    weather_tags=["any"],
    site_requirements=["path", "trees"],
    equipment=[],
    mechanic="sequence",
    bands={
        AgeBand.BAND_11_12: Band(
            title=None,
            steps=[
                TemplateStep(sequence=1, prompt_text="Walk to the first trail marker.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=2, prompt_text="Find a fence or boundary and follow it.", verify_mode="photo", prompt_id="p_fence", variable=True),
                TemplateStep(sequence=3, prompt_text="Count how many side paths you pass.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=4, prompt_text="Find a bench and sit for ten seconds.", verify_mode="photo", prompt_id="p_bench", variable=True),
                TemplateStep(sequence=5, prompt_text="Describe the next landmark before you reach it.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=6, prompt_text="Walk the return leg faster than the first.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=7, prompt_text="Tell an adult which part was hardest.", verify_mode="self", prompt_id=None, variable=True),
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="draft"),
)

# A "bare site" family — category "any", per the schema's bare-site note.
BARE_SITE_ANY_CATEGORY = MissionTemplate(
    template_id="fx_bare_site_any_category",
    title="Wherever you are",
    category="any",
    duration_bucket=20,
    weather_tags=["any"],
    site_requirements=["bare_site"],
    equipment=[],
    mechanic="imagine",
    bands={
        AgeBand.BAND_5_7: Band(
            title=None,
            steps=[
                TemplateStep(sequence=1, prompt_text="Look up and describe a cloud.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=2, prompt_text="Find something round nearby.", verify_mode="photo", prompt_id="p_round", variable=True),
                TemplateStep(sequence=3, prompt_text="Spin around three times.", verify_mode="self", prompt_id=None, variable=True),
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="draft"),
)

# Non-empty equipment, exercises equipment pass-through.
WITH_EQUIPMENT = MissionTemplate(
    template_id="fx_with_equipment",
    title="Pedal rhythm",
    category="cycling_track",
    duration_bucket=40,
    weather_tags=["dry"],
    site_requirements=["path"],
    equipment=["bicycle", "helmet"],
    mechanic="move",
    bands={
        AgeBand.BAND_8_10: Band(
            title=None,
            steps=[
                TemplateStep(sequence=1, prompt_text="Ride slowly to a tree you can see.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=2, prompt_text="Ride back, counting pedal pushes.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=3, prompt_text="Find your helmet and show it.", verify_mode="photo", prompt_id="p_helmet", variable=True),
                TemplateStep(sequence=4, prompt_text="Ride quickly back to the start.", verify_mode="self", prompt_id=None, variable=True),
                TemplateStep(sequence=5, prompt_text="Compare your two push counts.", verify_mode="self", prompt_id=None, variable=True),
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="draft"),
)

# One full three-band family, each band holding the full 7 steps for its
# bucket-60 shape — the only fixture shaped so build_mission (B29) can
# truncate the same band down to 5 or 3 steps rather than switching bands.
MULTI_BAND_FAMILY = MissionTemplate(
    template_id="fx_multi_band_family",
    title="Waterway watch",
    category="waterway_and_foreshore",
    duration_bucket=60,
    weather_tags=["any"],
    site_requirements=["water_adjacent", "path"],
    equipment=[],
    mechanic="find",
    bands={
        AgeBand.BAND_5_7: Band(
            title=None,
            steps=[
                TemplateStep(sequence=i, prompt_text=f"5-7 step {i} along the water.", verify_mode="self", prompt_id=None, variable=True)
                for i in range(1, 8)
            ],
        ),
        AgeBand.BAND_8_10: Band(
            title=None,
            steps=[
                TemplateStep(sequence=i, prompt_text=f"8-10 step {i} along the water.", verify_mode="self", prompt_id=None, variable=True)
                for i in range(1, 8)
            ],
        ),
        AgeBand.BAND_11_12: Band(
            title=None,
            steps=[
                TemplateStep(sequence=i, prompt_text=f"11-12 step {i} along the water.", verify_mode="self", prompt_id=None, variable=True)
                for i in range(1, 8)
            ],
        ),
    },
    safety_tags=["inherited"],
    review=Review(author="fixture", reviewed_by=None, status="reviewed"),
)

TEMPLATES: tuple[MissionTemplate, ...] = (
    BUCKET20_BAND_5_7_SELF,
    BUCKET20_BAND_5_7_PHOTO,
    BUCKET40_BAND_8_10,
    BUCKET60_BAND_11_12,
    BARE_SITE_ANY_CATEGORY,
    WITH_EQUIPMENT,
    MULTI_BAND_FAMILY,
)


#  MISSIONS  (final wire-shape objects, as generate_missions/build_mission would return)


MISSION_20MIN_5_7 = Mission(
    mission_id="fxm_20min_5_7",
    template_id=BUCKET20_BAND_5_7_PHOTO.template_id,
    title="Garden colours",
    age_band=AgeBand.BAND_5_7,
    estimated_minutes=20,
    equipment=[],
    steps=[
        Step(sequence=1, prompt_text="Find something green.", verify_mode=VerifyMode.PHOTO, prompt_id="p_green"),
        Step(sequence=2, prompt_text="Find something red.", verify_mode=VerifyMode.PHOTO, prompt_id="p_red"),
        Step(sequence=3, prompt_text="Smell a flower.", verify_mode=VerifyMode.SELF, prompt_id=None),
    ],
)

MISSION_40MIN_8_10 = Mission(
    mission_id="fxm_40min_8_10",
    template_id=BUCKET40_BAND_8_10.template_id,
    title="Equipment challenge",
    age_band=AgeBand.BAND_8_10,
    estimated_minutes=40,
    equipment=[],
    steps=[
        Step(sequence=1, prompt_text="Find the tallest goal post.", verify_mode=VerifyMode.PHOTO, prompt_id="p_goal_post"),
        Step(sequence=2, prompt_text="Count how many lines are on the field.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=3, prompt_text="Find something blue.", verify_mode=VerifyMode.PHOTO, prompt_id="p_blue"),
        Step(sequence=4, prompt_text="Do ten star jumps on the grass.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=5, prompt_text="Show me your favourite spot and say why.", verify_mode=VerifyMode.SELF, prompt_id=None),
    ],
)

MISSION_60MIN_11_12 = Mission(
    mission_id="fxm_60min_11_12",
    template_id=BUCKET60_BAND_11_12.template_id,
    title="Trail explorer",
    age_band=AgeBand.BAND_11_12,
    estimated_minutes=60,
    equipment=[],
    steps=[
        Step(sequence=1, prompt_text="Walk to the first trail marker.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=2, prompt_text="Find a fence or boundary and follow it.", verify_mode=VerifyMode.PHOTO, prompt_id="p_fence"),
        Step(sequence=3, prompt_text="Count how many side paths you pass.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=4, prompt_text="Find a bench and sit for ten seconds.", verify_mode=VerifyMode.PHOTO, prompt_id="p_bench"),
        Step(sequence=5, prompt_text="Describe the next landmark before you reach it.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=6, prompt_text="Walk the return leg faster than the first.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=7, prompt_text="Tell an adult which part was hardest.", verify_mode=VerifyMode.SELF, prompt_id=None),
    ],
)

MISSION_WITH_EQUIPMENT = Mission(
    mission_id="fxm_40min_8_10_equipment",
    template_id=WITH_EQUIPMENT.template_id,
    title="Pedal rhythm",
    age_band=AgeBand.BAND_8_10,
    estimated_minutes=40,
    equipment=["bicycle", "helmet"],
    steps=[
        Step(sequence=1, prompt_text="Ride slowly to a tree you can see.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=2, prompt_text="Ride back, counting pedal pushes.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=3, prompt_text="Find your helmet and show it.", verify_mode=VerifyMode.PHOTO, prompt_id="p_helmet"),
        Step(sequence=4, prompt_text="Ride quickly back to the start.", verify_mode=VerifyMode.SELF, prompt_id=None),
        Step(sequence=5, prompt_text="Compare your two push counts.", verify_mode=VerifyMode.SELF, prompt_id=None),
    ],
)

MISSIONS: tuple[Mission, ...] = (
    MISSION_20MIN_5_7,
    MISSION_40MIN_8_10,
    MISSION_60MIN_11_12,
    MISSION_WITH_EQUIPMENT,
)
