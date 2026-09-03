// Iteration 1 — component tests for TimeView (AC-2.1.2, AC-2.1.3, AC-2.2.1, AC-2.2.3).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  getContext: vi.fn()
}))

import { getContext } from '../../client/src/api'
import TimeView from '../../client/src/views/TimeView.vue'
import { useSearchStore } from '../../client/src/store'
import { makeSummary } from '../fixtures/combos'

let pinia

beforeEach(() => {
  pinia = createPinia()
  setActivePinia(pinia)
  vi.clearAllMocks()
  getContext.mockResolvedValue(makeSummary())
})

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: TimeView },
      { path: '/results', component: { template: '<div />' } }
    ]
  })
  const wrapper = mount(TimeView, { global: { plugins: [pinia, router] } })
  await flushPromises()
  return wrapper
}

describe('AC-2.1.2 — Duration input bounds', () => {
  it('TC-2.1.2-02 (UI) — the slider only accepts 20–120 in 5-minute steps', async () => {
    const wrapper = await mountView()
    const slider = wrapper.find('input[type="range"]')
    expect(slider.attributes('min')).toBe('20')
    expect(slider.attributes('max')).toBe('120')
    expect(slider.attributes('step')).toBe('5')
  })

  it('the plan note states the 20/40/60 buckets and the tie-down rule', async () => {
    const wrapper = await mountView()
    expect(wrapper.find('.plan-note').text()).toMatch(/20, 40 and 60 minutes/)
    expect(wrapper.find('.plan-note').text()).toMatch(/Ties at 30 or 50 min round to the lower plan/)
  })
})

describe('AC-2.1.3 — Entered duration and matched bucket are both shown', () => {
  it('TC-2.1.3-01 — 45 entered shows the 40-minute plan and the travel exclusion', async () => {
    const store = useSearchStore()
    store.durationMin = 45
    const wrapper = await mountView()
    expect(wrapper.find('.duration-value').text()).toBe('45 min') // entered value
    expect(wrapper.find('.plan-title').text()).toMatch(/Matched to a 40-minute plan/) // matched bucket
    expect(wrapper.text()).toMatch(/not including travel/i) // on-site only
  })

  it('TC-2.1.3-01 — a tie at 50 is displayed as the lower 40-minute plan', async () => {
    const store = useSearchStore()
    store.durationMin = 50
    const wrapper = await mountView()
    expect(wrapper.find('.plan-title').text()).toMatch(/Matched to a 40-minute plan/)
  })
})

describe('AC-2.2.1 — Forecast display for the chosen point', () => {
  it('current conditions are loaded for the chosen suburb on mount', async () => {
    const store = useSearchStore()
    store.suburb = 'Clayton'
    await mountView()
    expect(getContext).toHaveBeenCalledTimes(1)
    expect(store.context.available).toBe(true)
  })

  it('TC-2.2.1-03 (partial) — the Open-Meteo attribution is present while loading', async () => {
    const store = useSearchStore()
    store.suburb = 'Clayton'
    // hold the request open so the loading state stays rendered
    getContext.mockReturnValue(new Promise(() => {}))
    const wrapper = await mountView()
    expect(wrapper.text()).toMatch(/Open-Meteo/)
  })
})

describe('AC-2.2.3 — Missing weather is labelled, never invented', () => {
  it('TC-2.2.3-01 (UI) — a failed forecast shows the unavailable state with no invented values', async () => {
    const store = useSearchStore()
    store.suburb = 'Clayton'
    getContext.mockRejectedValue(new Error('timeout'))
    const wrapper = await mountView()
    expect(wrapper.text()).toMatch(/Weather unavailable/i)
    expect(wrapper.text()).toMatch(/conditions will be marked unavailable/i)
    expect(wrapper.find('.weather-main').text()).not.toMatch(/°C/)
  })
})
