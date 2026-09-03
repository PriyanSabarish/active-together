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
