// Iteration 1 — unit tests for client/src/store.js, mapped to the Test Case
// IDs in L1_AC_Test_Cases.docx. The backend API is mocked, so these tests
// verify the frontend contract: what is sent, and how responses are shown.
// TCs owned by the backend (recommend() fixtures, request validation) or not
// yet implemented in the UI are recorded as it.todo() for traceability.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  getContext: vi.fn()
}))

import { postRecommendations, getContext } from '../../client/src/api'
import {
  useSearchStore,
  matchBucket,
  mapCombo,
  categoryLabel,
  CATEGORY_META,
  SUBURB_COORDS
} from '../../client/src/store'
import { makeCombo, makeSummary, okResponse } from '../fixtures/combos'

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

// ---------------------------------------------------------------------------
// US 1.1 — Choose Location and Maximum Radius
// ---------------------------------------------------------------------------
describe('AC-1.1.2 — Radius and pilot boundary are enforced', () => {
  it('TC-1.1.2-01 (frontend) — the chosen radius and coordinates are sent to the API', async () => {
    postRecommendations.mockResolvedValue(okResponse([makeCombo()]))
    const store = useSearchStore()
    store.suburb = 'Melbourne'
    store.radiusKm = 3
    await store.fetchRecommendations()
    expect(postRecommendations).toHaveBeenCalledWith({
      latitude: SUBURB_COORDS.Melbourne.latitude,
      longitude: SUBURB_COORDS.Melbourne.longitude,
      radiusKm: 3,
      durationMin: store.durationMin
    })
  })

  it.todo('TC-1.1.2-02 — inclusive 5 km distance boundary (backend query logic; pytest with seeded places)')
  it.todo('TC-1.1.2-03 — radius 7 rejected by request validation (backend A15; pytest)')
})

describe('AC-1.1.3 — Out-of-scope location is explained, not empty', () => {
  it('TC-1.1.3-01 (store) — an out_of_bounds response sets its own state, not zero-results', async () => {
    postRecommendations.mockResolvedValue({
      status: 'out_of_bounds',
      combos: [],
      message: 'Selected location is outside the active pilot area.'
    })
    const store = useSearchStore()
    store.suburb = 'Melbourne'
    await store.fetchRecommendations()
    expect(store.status).toBe('out_of_bounds')
    expect(store.message).toMatch(/outside the active pilot area/i)
    expect(store.results).toHaveLength(0)
  })

  it('TC-1.1.3-02 (store) — zero results is a distinct state from out-of-scope', async () => {
    postRecommendations.mockResolvedValue({ status: 'zero_results', combos: [] })
    const store = useSearchStore()
    store.suburb = 'Melbourne'
    await store.fetchRecommendations()
    expect(store.status).toBe('zero_results')
    expect(store.status).not.toBe('out_of_bounds')
  })
})

// ---------------------------------------------------------------------------
// US 1.2 / US 1.3 — Candidate display and category mapping
// ---------------------------------------------------------------------------
describe('AC-1.2.2 — Each candidate shows name, category and distance', () => {
  it('TC-1.2.2-01 — mapped combo carries display name, category label and distance', () => {
    const r = mapCombo(makeCombo(), { radiusKm: 5 })
    expect(r.name).toBe('Argyle Square')
    expect(r.categoryLabel).toBe('Park and garden')
    expect(r.distanceKm).toBeCloseTo(0.4)
    expect(r.reasons[0]).toMatch(/About .* away/)
  })

  it('TC-1.2.2-02 — a record with no official name falls back to its category label', () => {
    const r = mapCombo(makeCombo({ place: { display_name: null, activity_category: 'playground' } }), { radiusKm: 5 })
    expect(r.unnamed).toBe(true)
    expect(r.name).toBe('Playground')
    expect(r.recordId).toBeNull()
  })

  it('TC-1.2.2-02 — a pipeline-generated "Unnamed ..." label is shown without the word Unnamed', () => {
    const r = mapCombo(makeCombo({ place: { display_name: 'Unnamed Park - Monash - 643568', activity_category: 'park_and_garden' } }), { radiusKm: 5 })
    expect(r.unnamed).toBe(true)
    expect(r.name).toBe('Park - Monash')
    expect(r.recordId).toBe('643568')
    expect(r.name).not.toMatch(/unnamed/i)
  })
})

describe('AC-1.2.3 — Unverified attributes are omitted, never inferred', () => {
  it('TC-1.2.3-01 — no hours, cost, accessibility or placeholder value in the mapped card data', () => {
    const r = mapCombo(makeCombo(), { radiusKm: 5 })
    const text = JSON.stringify(r).toLowerCase()
    expect(text).not.toMatch(/open(s|ing)? hours|price|"cost"|accessib|\bfree\b|\bunknown\b/)
  })
})

describe('AC-1.3.1 — Every result carries a mapped category', () => {
  it('TC-1.3.1-01 — all seven approved categories map to exactly one label', () => {
    const approved = [
      'playground', 'park_and_garden', 'picnic_day_use',
      'sports_ground', 'court', 'skate_bmx', 'trail_access'
    ]
    expect(Object.keys(CATEGORY_META).sort()).toEqual([...approved].sort())
    for (const c of approved) {
      expect(categoryLabel(c)).toBeTruthy()
      expect(typeof categoryLabel(c)).toBe('string')
    }
  })

  it('TC-1.3.1-02 (data) — the card copy claims an opportunity, not a verified facility', () => {
    const r = mapCombo(makeCombo(), { radiusKm: 5 })
    expect(r.expect).toMatch(/suggestion/i)
    expect(r.expect).toMatch(/not verified/i)
  })

  it.todo('TC-1.3.2-01 / TC-1.3.2-02 — excluded record types never surface (data pipeline + backend; validated on vicmap_app_ready.csv and API responses)')
})

// ---------------------------------------------------------------------------
// US 2.1 — Date, time and duration
// ---------------------------------------------------------------------------
describe('AC-2.1.2 — Duration maps to a template bucket deterministically', () => {
  // Full table from TC-2.1.2-01, including both tie-down cases.
  it.each([
    [20, 20], [25, 20], [30, 20], [35, 40], [45, 40],
    [50, 40], [55, 60], [90, 60], [120, 60]
  ])('TC-2.1.2-01 — %i minutes matches the %i-minute bucket', (input, bucket) => {
    expect(matchBucket(input)).toBe(bucket)
  })

  it('TC-2.1.2-01 — the store planMin getter uses the same matching', () => {
    const store = useSearchStore()
    store.durationMin = 50
    expect(store.planMin).toBe(40)
  })

  it.todo('TC-2.1.2-02 — 15 / 125 / 42.5 rejected by request validation (backend A15; the UI slider bounds are asserted in time.view.spec.js)')
})

describe('AC-2.1.1 — Only forecast-covered times can be selected', () => {
  it.todo('TC-2.1.1-01 / TC-2.1.1-02 — the current UI supports "right now" only (no date/time selector); becomes testable when time selection ships')
})

// ---------------------------------------------------------------------------
// US 2.2 / US 2.3 — Weather, UV and air quality display
// ---------------------------------------------------------------------------
describe('AC-2.2.2 — Poor conditions de-prioritise rather than hide', () => {
  it.todo('TC-2.2.2-01/-02/-03 — 60% precipitation and 40 km/h thresholds (backend recommend(); pytest fixtures)')

  it('TC-2.2.2 (frontend) — a deprioritised combo stays visible and carries a warning badge', () => {
    const r = mapCombo(makeCombo({
      tier: 'deprioritised',
      environmental_summary: makeSummary({ warnings: ['High chance of rain around that time'] })
    }), { radiusKm: 5 })
    expect(r.tier).toBe('deprioritised')
    expect(r.badge.type).toBe('warn')
    expect(r.badge.label).toBe('rain risk')
    expect(r.reasons.join(' ')).toMatch(/rain/i)
  })

  it('TC-2.2.2-04 — warning wording is informational and makes no safety claim', () => {
    const r = mapCombo(makeCombo({
      tier: 'deprioritised',
      environmental_summary: makeSummary({ warnings: ['Wind gusts around that time'] })
    }), { radiusKm: 5 })
    const text = JSON.stringify(r).toLowerCase()
    expect(text).not.toMatch(/\bguaranteed?\b|\bsafe to\b|100% safe|do not go|must not/)
  })
})

describe('AC-2.2.3 — Missing weather is labelled, never invented', () => {
  it('TC-2.2.3-01 (frontend) — an unavailable summary is labelled and no value is invented', () => {
    const r = mapCombo(makeCombo({ environmental_summary: { available: false } }), { radiusKm: 5 })
    expect(r.badge.label).toBe('weather unavailable')
    expect(r.conditions).toEqual([
      { icon: 'unknown', text: 'Weather data is unavailable for this time.' }
    ])
    expect(r.reasons.join(' ')).toMatch(/unavailable/i)
    const text = JSON.stringify(r.conditions)
    expect(text).not.toMatch(/°C|% chance|km\/h/)
  })

  it('TC-2.2.3-01 (store) — candidates are still returned when weather is unavailable', async () => {
    postRecommendations.mockResolvedValue(okResponse([
      makeCombo({ environmental_summary: { available: false } })
    ]))
    const store = useSearchStore()
    store.suburb = 'Clayton'
    await store.fetchRecommendations()
    expect(store.status).toBe('ok')
    expect(store.results).toHaveLength(1)
  })
})

describe('AC-2.3.1 — High UV adds a reminder without changing ranking', () => {
  it('TC-2.3.1-01 (frontend) — a UV reminder shows sun protection and the tier stays normal', () => {
    const r = mapCombo(makeCombo({
      environmental_summary: makeSummary({ uv_index: 3, reminders: ['UV is 3 or above — sun protection suggested'] })
    }), { radiusKm: 5 })
    expect(r.tier).toBe('normal')
    expect(r.badge.type).toBe('good')
    const uvRow = r.conditions.find((c) => c.icon === 'uv')
    expect(uvRow.text).toMatch(/sun protection/i)
  })

  it('TC-2.3.1-02 (frontend) — below the threshold no reminder is shown', () => {
    const r = mapCombo(makeCombo({
      environmental_summary: makeSummary({ uv_index: 2.9, reminders: [] })
    }), { radiusKm: 5 })
    const uvRow = r.conditions.find((c) => c.icon === 'uv')
    expect(uvRow.text).toMatch(/low sun risk/i)
    expect(uvRow.text).not.toMatch(/sun protection/i)
  })

  it.todo('TC-2.3.1-01/-02 — uv_index 3.0 / 2.9 threshold itself (backend recommend(); pytest)')
})

describe('AC-2.3.2 — Poor air quality de-prioritises the candidate', () => {
  it.todo('TC-2.3.2-01/-02/-03 — PM2.5 25 / PM10 80 thresholds (backend recommend(); pytest)')

  it('TC-2.3.2 (frontend) — a particle warning renders as an elevated air-quality row and warn badge', () => {
    const r = mapCombo(makeCombo({
      tier: 'deprioritised',
      environmental_summary: makeSummary({ pm25: 30, warnings: ['Fine particle levels are elevated'] })
    }), { radiusKm: 5 })
    expect(r.badge.label).toBe('air quality')
    const airRow = r.conditions.find((c) => /air quality/i.test(c.text))
    expect(airRow.text).toMatch(/^Elevated/)
  })
})

describe('AC-2.3.3 — Missing readings are labelled and carry no medical advice', () => {
  it('TC-2.3.3-01 (frontend) — missing PM values are omitted rather than defaulted', () => {
    const r = mapCombo(makeCombo({
      environmental_summary: makeSummary({ pm25: null, pm10: null })
    }), { radiusKm: 5 })
    expect(r.conditions.some((c) => /PM2\.5|PM10/.test(c.text))).toBe(false)
  })

  it('TC-2.3.3-02 — no medical advice appears in any generated copy', () => {
    const combos = [
      makeCombo(),
      makeCombo({ tier: 'deprioritised', environmental_summary: makeSummary({ warnings: ['Fine particle levels are elevated'] }) }),
      makeCombo({ environmental_summary: { available: false } })
    ]
    for (const c of combos) {
      const text = JSON.stringify(mapCombo(c, { radiusKm: 5 })).toLowerCase()
      expect(text).not.toMatch(/asthma|doctor|medical|health risk|breathing difficulty|stay indoors/)
    }
  })
})

// ---------------------------------------------------------------------------
// US 3.1 — Up to three, deterministic, honest empty states
// ---------------------------------------------------------------------------
describe('AC-3.1.1 / AC-3.1.2 — Eligibility and ordering', () => {
  it.todo('TC-3.1.1-01 — four eligibility conditions enforced independently (backend recommend(); pytest)')
  it.todo('TC-3.1.2-01 — cap at three (backend; the frontend renders whatever the API returns — rendering is asserted in results.view.spec.js)')
  it.todo('TC-3.1.2-03 — tier → distance → name ordering (backend; frontend must preserve API order, asserted in results.view.spec.js)')

  it('TC-3.1.2-02 (frontend) — identical input produces identical mapped output', async () => {
    const combos = [makeCombo(), makeCombo({ place: { place_id: 'p-002', display_name: 'Fawkner Park', distance_m: 600 } })]
    postRecommendations.mockResolvedValue(okResponse(combos))
    const store = useSearchStore()
    store.suburb = 'Melbourne'
    await store.fetchRecommendations()
    const first = store.results.map((r) => r.id)
    await store.fetchRecommendations()
    const second = store.results.map((r) => r.id)
    expect(second).toEqual(first)
  })
})

describe('AC-3.1.4 — Dataset failure is its own state', () => {
  it('TC-3.1.4-01 (store) — an API failure sets an error state, never an empty result list', async () => {
    postRecommendations.mockRejectedValue(
      new Error('The places dataset is temporarily unavailable. Please try again shortly.')
    )
    const store = useSearchStore()
    store.suburb = 'Melbourne'
    await store.fetchRecommendations()
    expect(store.status).toBe('error')
    expect(store.status).not.toBe('zero_results')
    expect(store.error).toMatch(/temporarily unavailable/i)
  })
})

// ---------------------------------------------------------------------------
// US 3.2 / US 3.3 — Card facts and explanations
// ---------------------------------------------------------------------------
describe('AC-3.2.1 — Each card carries the verified facts', () => {
  it('TC-3.2.1-01 (frontend) — name, category, distance and environmental summary are all mapped', () => {
    const r = mapCombo(makeCombo(), { radiusKm: 5 })
    expect(r.name).toBeTruthy()
    expect(r.categoryLabel).toBeTruthy()
    expect(r.distanceKm).toBeGreaterThan(0)
    expect(r.conditions.length).toBeGreaterThan(0)
  })
})

describe('AC-3.2.2 — Unverified facts stay off the card', () => {
  it('TC-3.2.2-01 — no hours, price, facility or capacity fields exist in the card model', () => {
    const r = mapCombo(makeCombo(), { radiusKm: 5 })
    for (const key of Object.keys(r)) {
      expect(key).not.toMatch(/hours|price|cost|facilit|capacity/i)
    }
  })

  it('TC-3.2.2-02 — the generated-label flag is preserved for provenance', () => {
    const named = mapCombo(makeCombo(), { radiusKm: 5 })
    const generated = mapCombo(makeCombo({ place: { display_name: '' } }), { radiusKm: 5 })
    expect(named.unnamed).toBe(false)
    expect(generated.unnamed).toBe(true)
  })
})

describe('AC-3.3.1 / AC-3.3.2 — Explanations use only decision inputs', () => {
  it('TC-3.3.1-01 (frontend) — reasons reference distance, radius, duration and conditions only', () => {
    const r = mapCombo(makeCombo(), { radiusKm: 5 })
    expect(r.reasons[0]).toMatch(/km/)
    expect(r.reasons[1]).toMatch(/-min window using the .*-min plan/)
  })

  it('TC-3.3.2-01 (frontend) — with weather unavailable the explanation names the gap, never estimates', () => {
    const r = mapCombo(makeCombo({ environmental_summary: { available: false } }), { radiusKm: 5 })
    expect(r.reasons).toContain('Weather data is unavailable for this time.')
    expect(r.reasons.join(' ')).not.toMatch(/typical|usually|around \d+°C|estimated/i)
  })

  it('TC-3.3.2-02 — no facility, hours, cost or safety claim in reasons across varied fixtures', () => {
    const fixtures = [
      makeCombo(),
      makeCombo({ tier: 'deprioritised', environmental_summary: makeSummary({ warnings: ['Wind gusts around that time'] }) }),
      makeCombo({ environmental_summary: { available: false } })
    ]
    for (const c of fixtures) {
      const text = mapCombo(c, { radiusKm: 5 }).reasons.join(' ').toLowerCase()
      expect(text).not.toMatch(/open(s|ing)? hours|\$|cost|toilet|caf|playground equipment|guaranteed|safe for/)
    }
  })
})

// ---------------------------------------------------------------------------
// Context loading for the time screen (supports AC-2.2.1 display)
// ---------------------------------------------------------------------------
describe('AC-2.2.1 — Forecast is retrieved for the selected place', () => {
  it.todo('TC-2.2.1-01 — values match a direct Open-Meteo call (integration; backend)')
  it.todo('TC-2.2.1-02 — repeat request served from cache (backend A9)')

  it('loadContext requests conditions for the chosen coordinates', async () => {
    getContext.mockResolvedValue(makeSummary())
    const store = useSearchStore()
    store.suburb = 'Clayton'
    await store.loadContext()
    expect(getContext).toHaveBeenCalledWith(SUBURB_COORDS.Clayton)
    expect(store.context.available).toBe(true)
  })

  it('a failed context call degrades to an unavailable state instead of throwing', async () => {
    getContext.mockRejectedValue(new Error('boom'))
    const store = useSearchStore()
    store.suburb = 'Clayton'
    await store.loadContext()
    expect(store.context).toEqual({ available: false })
  })
})
