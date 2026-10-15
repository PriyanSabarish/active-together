// Backend-contract fixtures for frontend unit tests.
// Shapes mirror POST /recommendations combos (server/app/models.py).

export function makeSummary(overrides = {}) {
  return {
    available: true,
    temp_c: 21,
    precip_prob: 0.1,
    wind_gust_kmh: 15,
    uv_index: 2,
    pm25: 8,
    pm10: 15,
    warnings: [],
    reminders: [],
    ...overrides
  }
}

export function makeCombo(overrides = {}) {
  const { place: placeOverrides, environmental_summary: summaryOverrides, ...rest } = overrides
  return {
    place: {
      place_id: 'p-001',
      display_name: 'Argyle Square',
      activity_category: 'park_and_garden',
      lga_name: 'Melbourne',
      latitude: -37.8025,
      longitude: 144.9662,
      distance_m: 400,
      ...placeOverrides
    },
    environmental_summary: makeSummary(summaryOverrides),
    tier: 'normal',
    duration_bucket: 40,
    travel_min: 8, // one way
    entered_duration_min: 45,
    activity_type: 'Open play and a walk',
    combo_template: '40-minute park visit',
    explanation: 'About 0.4 km away and fits your 45-minute window with the 40-minute plan.',
    ...rest
  }
}

export function okResponse(combos, extra = {}) {
  return { status: 'ok', combos, ...extra }
}

// A spread result: one place near, one mid-range, one far (7, 16, 27 min one way).
export function spreadResponse() {
  return okResponse(
    [
      makeCombo({ place: { place_id: 's-1', display_name: 'Near Park', distance_m: 500 }, travel_min: 7 }),
      makeCombo({ place: { place_id: 's-2', display_name: 'Mid Oval', activity_category: 'sports_ground', distance_m: 1300 }, travel_min: 16 }),
      makeCombo({ place: { place_id: 's-3', display_name: 'Far Playground', activity_category: 'playground', distance_m: 2200 }, travel_min: 27 })
    ],
    { ranking_mode: 'spread' }
  )
}

export function makeTravel(overrides = {}) {
  return {
    mode: 'walking',
    out_min: 10,
    back_min: 10,
    on_site_min: 40,
    total_min: 60,
    source: 'openrouteservice',
    back_from_outbound: true,
    ...overrides
  }
}
