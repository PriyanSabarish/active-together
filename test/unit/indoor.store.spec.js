// Story 9.3 — indoor places come from POST /recommendations (setting indoor_place).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  postIndoorPlaces: vi.fn(),
  getContext: vi.fn()
}))

import { postIndoorPlaces } from '../../client/src/api'
import { useSearchStore, mapIndoorPlace } from '../../client/src/store'

const SERVER_PLACE = { place_id: 'in-1', display_name: 'Carlton Library', category: 'library', distance_m: 820, unverified: true }

function storeAt() {
  const store = useSearchStore()
  store.suburb = 'Carlton'
  store.radiusKm = 5
  return store
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('indoor place search', () => {
  it('TC-9.3-01 — maps the server list, in order, each unverified', async () => {
    postIndoorPlaces.mockResolvedValue({
      status: 'ok',
      places: [SERVER_PLACE, { ...SERVER_PLACE, place_id: 'in-2', display_name: 'Leisure Centre', category: 'leisure_centre', distance_m: 1600 }]
    })
    const store = storeAt()
    await store.searchIndoor()
    expect(postIndoorPlaces).toHaveBeenCalledWith(expect.objectContaining({ radiusKm: 5 }))
    expect(store.indoorStatus).toBe('ok')
    expect(store.indoorResults.map((p) => p.id)).toEqual(['in-1', 'in-2'])
    expect(store.indoorResults[0]).toMatchObject({ name: 'Carlton Library', categoryLabel: 'library', distanceKm: 0.8, unverified: true })
    expect(store.indoorPlace('in-2').name).toBe('Leisure Centre')
  })

  it('TC-9.3-02 — zero results leaves an empty list with a zero_results status', async () => {
    postIndoorPlaces.mockResolvedValue({ status: 'zero_results', places: [], suggestions: ['larger_radius', 'at_home'] })
    const store = storeAt()
    await store.searchIndoor()
    expect(store.indoorStatus).toBe('zero_results')
    expect(store.indoorResults).toEqual([])
  })

  it('TC-9.3-03 — a failed request sets an error and can be retried', async () => {
    postIndoorPlaces.mockRejectedValueOnce(new Error('Could not reach the service.'))
    const store = storeAt()
    await store.searchIndoor()
    expect(store.indoorStatus).toBe('error')
    expect(store.indoorError).toMatch(/Could not reach/)
    postIndoorPlaces.mockResolvedValue({ status: 'ok', places: [SERVER_PLACE] })
    await store.searchIndoor()
    expect(store.indoorStatus).toBe('ok')
  })

  it('TC-9.3-04 — with no location nothing is requested', async () => {
    const store = useSearchStore()
    await store.searchIndoor()
    expect(postIndoorPlaces).not.toHaveBeenCalled()
    expect(store.indoorStatus).toBe('idle')
  })

  it('TC-9.3-05 — a place without coordinates still maps', () => {
    expect(mapIndoorPlace(SERVER_PLACE)).toMatchObject({ latitude: null, longitude: null })
  })
})
