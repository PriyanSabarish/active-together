// Iteration 1 — component tests for ResultsView
// (AC-1.1.3, AC-1.2.2, AC-3.1.2 rendering, AC-3.1.3, AC-3.1.4, AC-3.2.1).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  getContext: vi.fn()
}))

import { postRecommendations } from '../../client/src/api'
import ResultsView from '../../client/src/views/ResultsView.vue'
import { useSearchStore } from '../../client/src/store'
import { makeCombo, makeTravel, okResponse } from '../fixtures/combos'

let pinia

beforeEach(() => {
  pinia = createPinia()
  setActivePinia(pinia)
  vi.clearAllMocks()
})

function threeCombos() {
  return [
    makeCombo(),
    makeCombo({ place: { place_id: 'p-002', display_name: 'Fawkner Park', distance_m: 600 } }),
    makeCombo({
      tier: 'deprioritised',
      place: { place_id: 'p-003', display_name: 'Merri Creek Trail', activity_category: 'trail_access', distance_m: 1200 },
      environmental_summary: { available: true, warnings: ['Wind gusts around that time'], reminders: [] }
    })
  ]
}

async function mountResults(response, { suburb = 'Melbourne', radiusKm = 5 } = {}) {
  if (response instanceof Error) postRecommendations.mockRejectedValue(response)
  else postRecommendations.mockResolvedValue(response)
  const store = useSearchStore()
  store.suburb = suburb
  store.radiusKm = radiusKm
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: ResultsView },
      { path: '/place/:id', component: { template: '<div />' } }
    ]
  })
  const wrapper = mount(ResultsView, { global: { plugins: [pinia, router] } })
  await flushPromises()
  return { wrapper, store }
}

describe('AC-1.1.3 — Out-of-scope location is explained, not empty', () => {
  it('TC-1.1.3-01 — an out_of_bounds response shows the pilot-scope message naming the councils', async () => {
    const { wrapper } = await mountResults({
      status: 'out_of_bounds',
      combos: [],
      message: 'Selected location is outside the active pilot area.'
    })
    expect(wrapper.find('.empty-title').text()).toBe('Outside the pilot area')
    expect(wrapper.find('.empty-text').text()).toMatch(/Melbourne, Monash and Melton/)
    // the generic zero-results screen is NOT shown
    expect(wrapper.text()).not.toMatch(/Nothing within/)
  })

  it('TC-1.1.3-02 — zero results shows the widen-radius screen, visibly different from out-of-scope', async () => {
    const { wrapper } = await mountResults({ status: 'zero_results', combos: [] }, { radiusKm: 3 })
    expect(wrapper.find('.empty-title').text()).toMatch(/Nothing within 3 km/)
    expect(wrapper.find('.empty-text').text()).toMatch(/wider search radius/i)
    expect(wrapper.find('.widen-btn').text()).toMatch(/Search 5 km instead/)
    expect(wrapper.text()).not.toMatch(/Outside the pilot area/)
  })
})

describe('AC-3.1.3 — Thin and empty results are handled honestly', () => {
  it('TC-3.1.3-01 — two combos render exactly two cards with no padding', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos().slice(0, 2)))
    expect(wrapper.findAll('.result-card')).toHaveLength(2)
    expect(wrapper.find('.footnote').text()).toMatch(/Only two places/)
  })

  it('TC-3.1.3-01 — a single combo renders one card and an explanatory footnote', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos().slice(0, 1)))
    expect(wrapper.findAll('.result-card')).toHaveLength(1)
    expect(wrapper.find('.footnote').text()).toMatch(/Only one place/)
  })

  it('TC-3.1.3-02 — the zero-results action re-runs the search with a wider radius', async () => {
    const { wrapper, store } = await mountResults({ status: 'zero_results', combos: [] }, { radiusKm: 3 })
    postRecommendations.mockResolvedValue(okResponse(threeCombos().slice(0, 1)))
    await wrapper.find('.widen-btn').trigger('click')
    await flushPromises()
    expect(store.radiusKm).toBe(5)
    expect(wrapper.findAll('.result-card')).toHaveLength(1)
  })
})

describe('AC-3.1.4 — Dataset failure is its own state', () => {
  it('TC-3.1.4-01 — an API failure renders the error state with retry, not zero results', async () => {
    const { wrapper } = await mountResults(
      new Error('The places dataset is temporarily unavailable. Please try again shortly.')
    )
    expect(wrapper.find('.empty-title').text()).toBe("We couldn't load places")
    expect(wrapper.find('.empty-text').text()).toMatch(/temporarily unavailable/i)
    expect(wrapper.find('.widen-btn').text()).toBe('Try again')
    expect(wrapper.text()).not.toMatch(/Nothing within/)
  })
})

describe('AC-1.2.2 / AC-3.2.1 — Card facts', () => {
  it('TC-1.2.2-01 / TC-3.2.1-01 — every card shows name, category and distance', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos()))
    const cards = wrapper.findAll('.result-card')
    expect(cards).toHaveLength(3)
    for (const card of cards) {
      expect(card.find('.place-name').text()).toBeTruthy()
      expect(card.find('.place-meta').text()).toMatch(/·\s*[\d.]+ km/)
    }
  })

  it('every card shows its travel time one way', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos()))
    for (const card of wrapper.findAll('.result-card')) {
      expect(card.find('.place-meta').text()).toMatch(/\d+ min walk/)
    }
  })

})

describe('AC-3.1.2 — Order comes from the backend and is preserved', () => {
  it('TC-3.1.2-03 (frontend) — cards render in exactly the order the API returned', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos()))
    const names = wrapper.findAll('.place-name').map((n) => n.text())
    expect(names).toEqual(['Argyle Square', 'Fawkner Park', 'Merri Creek Trail'])
  })

  it('TC-3.1.2 (frontend) — a deprioritised combo stays visible with a warning badge', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos()))
    const last = wrapper.findAll('.result-card')[2]
    expect(last.text()).toContain('Merri Creek Trail')
    expect(last.text()).toMatch(/windy/i)
  })
})

describe('Story 3.2 — server travel block', () => {
  it('TC-3.2-01 — the travel block is mapped onto each place, with its own plan length', async () => {
    const { store } = await mountResults(
      okResponse([
        makeCombo({ travel: makeTravel() }),
        makeCombo({
          place: { place_id: 'p-002', display_name: 'Fawkner Park' },
          travel: makeTravel({ on_site_min: 20, source: 'estimate' })
        })
      ])
    )
    expect(store.results[0].travel).toMatchObject({ outMin: 10, backMin: 10, onSiteMin: 40, totalMin: 60, source: 'openrouteservice' })
    expect(store.results[1].travel).toMatchObject({ onSiteMin: 20, source: 'estimate' })
  })

  it('TC-3.2-02 — attribution shows with travel times, and a combo without a block still renders', async () => {
    const withTravel = await mountResults(okResponse([makeCombo({ travel: makeTravel() })]))
    expect(withTravel.wrapper.find('.attribution').text()).toMatch(/OpenRouteService.*OpenStreetMap/s)
    pinia = createPinia()
    setActivePinia(pinia)
    const without = await mountResults(okResponse([makeCombo()]))
    expect(without.store.results[0].travel).toBeNull()
    expect(without.wrapper.find('.result-card').exists()).toBe(true)
    expect(without.wrapper.find('.attribution').exists()).toBe(false)
  })
})

describe('Story 9.1 — Try Indoors suggestion', () => {
  it('TC-9.1-01 — shown when suggest_indoors is true, with the results still listed', async () => {
    const { wrapper } = await mountResults(okResponse([makeCombo()], { suggest_indoors: true }))
    expect(wrapper.find('.try-indoors').exists()).toBe(true)
    expect(wrapper.findAll('.result-card')).toHaveLength(1)
  })

  it('TC-9.1-02 — hidden when suggest_indoors is false or missing', async () => {
    const { wrapper } = await mountResults(okResponse([makeCombo()], { suggest_indoors: false }))
    expect(wrapper.find('.try-indoors').exists()).toBe(false)
  })

  it('TC-9.1-03 — dismissing hides it and keeps the results', async () => {
    const { wrapper } = await mountResults(okResponse([makeCombo()], { suggest_indoors: true }))
    await wrapper.find('.try-x').trigger('click')
    expect(wrapper.find('.try-indoors').exists()).toBe(false)
    expect(wrapper.findAll('.result-card')).toHaveLength(1)
  })

  it('TC-9.1-04 — Try Indoors returns to Start with the Outdoors / Indoors menu to open', async () => {
    const { wrapper, store } = await mountResults(okResponse([makeCombo()], { suggest_indoors: true }))
    await wrapper.find('.try-go').trigger('click')
    expect(store.openSettingMenu).toBe(true)
  })
})
