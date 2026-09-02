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
import { makeCombo, okResponse } from '../fixtures/combos'

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
      expect(card.find('.reason').text()).toBeTruthy()
    }
  })

  it('TC-3.2.1-01 — each card shows the matched bucket and combo template', async () => {
    const { wrapper } = await mountResults(okResponse(threeCombos().slice(0, 1)))
    expect(wrapper.find('.duration-line').text()).toMatch(/40 min on-site · 40-minute park visit/)
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
