// Iteration 1 — unit tests for client/src/api.js (request building and
// error mapping; supports AC-1.1.2 payload contract and AC-3.1.4 messaging).

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { postRecommendations, getContext, ApiError } from '../../client/src/api'

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
      duration_min: 45
    })
  })

  it('GET /data/context carries the point as lat/lon query params', async () => {
    fetch.mockResolvedValue(jsonResponse({ available: true }))
    await getContext({ latitude: -37.9, longitude: 145.1 })
    expect(fetch.mock.calls[0][0]).toMatch(/\/data\/context\?lat=-37\.9&lon=145\.1$/)
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
