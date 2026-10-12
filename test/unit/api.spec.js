// Iteration 1 — unit tests for client/src/api.js (request building and
// error mapping; supports AC-1.1.2 payload contract and AC-3.1.4 messaging).

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { postRecommendations, postIndoorPlaces, postHomeMissions, getContext, searchAddresses, ApiError } from '../../client/src/api'

function jsonResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body)
  }
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('POST /recommendations request contract (AC-1.1.2)', () => {
  it('sends latitude, longitude, radius_km and duration_min in snake_case', async () => {
    fetch.mockResolvedValue(jsonResponse({ status: 'ok', combos: [] }))
    await postRecommendations({ latitude: -37.8136, longitude: 144.9631, radiusKm: 3, durationMin: 45 })
    const [url, init] = fetch.mock.calls[0]
    expect(url).toMatch(/\/recommendations$/)
    expect(JSON.parse(init.body)).toEqual({
      latitude: -37.8136,
      longitude: 144.9631,
      radius_km: 3,
      duration_min: 45,
      travel_mode: 'walking',
      excluded_categories: []
    })
  })

  it('GET /data/context carries the point as lat/lon query params', async () => {
    fetch.mockResolvedValue(jsonResponse({ available: true }))
    await getContext({ latitude: -37.9, longitude: 145.1 })
    expect(fetch.mock.calls[0][0]).toMatch(/\/data\/context\?lat=-37\.9&lon=145\.1$/)
  })

  it('GET /data/context unwraps the { status, context } shape to the flat readings', async () => {
    fetch.mockResolvedValue(jsonResponse({ status: 'ok', context: { available: true, temp_c: 22.3, uv_index: 8.1 } }))
    await expect(getContext({ latitude: -37.9, longitude: 145.1 }))
      .resolves.toEqual({ available: true, temp_c: 22.3, uv_index: 8.1 })
  })

  it('GET /data/context still accepts the older flat shape', async () => {
    fetch.mockResolvedValue(jsonResponse({ available: true, temp_c: 18 }))
    await expect(getContext({ latitude: -37.9, longitude: 145.1 })).resolves.toEqual({ available: true, temp_c: 18 })
  })

  it('encodes address autocomplete query parameters', async () => {
    fetch.mockResolvedValue(jsonResponse({ suggestions: [] }))
    await searchAddresses('1 Centre Road')
    expect(fetch.mock.calls[0][0]).toMatch(/\/locations\/autocomplete\?q=1\+Centre\+Road&limit=5$/)
  })
})

describe('Error mapping (AC-3.1.4 — dataset failure is its own state)', () => {
  it('a 503 maps to the dataset-unavailable message', async () => {
    fetch.mockResolvedValue(jsonResponse({ detail: 'dataset not loaded' }, 503))
    await expect(postRecommendations({ latitude: 0, longitude: 0, radiusKm: 5, durationMin: 45 }))
      .rejects.toMatchObject({
        status: 503,
        message: expect.stringMatching(/places dataset is temporarily unavailable/i)
      })
  })

  it('a 422 validation error surfaces the backend detail (AC-2.1.2 / A15)', async () => {
    fetch.mockResolvedValue(jsonResponse({ detail: 'radius_km must be one of 3, 5, 10' }, 422))
    await expect(postRecommendations({ latitude: 0, longitude: 0, radiusKm: 7, durationMin: 45 }))
      .rejects.toMatchObject({ message: 'radius_km must be one of 3, 5, 10' })
  })

  it('a network failure produces a connection message, not a raw exception', async () => {
    fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(getContext({ latitude: 0, longitude: 0 }))
      .rejects.toMatchObject({
        status: 0,
        message: expect.stringMatching(/could not reach the active together service/i)
      })
  })

  it('errors are ApiError instances carrying the HTTP status', async () => {
    fetch.mockResolvedValue(jsonResponse({}, 500))
    const err = await postRecommendations({ latitude: 0, longitude: 0, radiusKm: 5, durationMin: 45 }).catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(500)
  })
})

describe('POST /recommendations for indoor places (story 9.3)', () => {
  it('sends setting indoor_place with coordinates cut to 4 dp and no duration or travel fields', async () => {
    fetch.mockResolvedValue(jsonResponse({ status: 'ok', places: [] }))
    await postIndoorPlaces({ latitude: -37.813612345, longitude: 144.963198765, radiusKm: 5 })
    const [url, init] = fetch.mock.calls[0]
    expect(url).toMatch(/\/recommendations$/)
    expect(JSON.parse(init.body)).toEqual({ setting: 'indoor_place', latitude: -37.8136, longitude: 144.9632, radius_km: 5 })
  })
})

describe('POST /recommendations for at-home activities (story 9.2)', () => {
  it('sends setting home, the time and the age band, and no location', async () => {
    fetch.mockResolvedValue(jsonResponse({ setting: 'home', missions: [] }))
    await postHomeMissions({ durationMin: 15, ageBand: '8-10', recentTemplateIds: ['t1'] })
    const [url, init] = fetch.mock.calls[0]
    expect(url).toMatch(/\/recommendations$/)
    const body = JSON.parse(init.body)
    expect(body).toEqual({ setting: 'home', duration_min: 15, age_band: '8-10', recent_template_ids: ['t1'] })
    expect(body).not.toHaveProperty('latitude')
    expect(body).not.toHaveProperty('longitude')
    expect(body).not.toHaveProperty('radius_km')
  })
})
