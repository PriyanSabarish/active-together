// Iteration 1 — component tests for DetailView (AC-3.2.1, AC-3.2.2, AC-3.3.1).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  getContext: vi.fn()
}))

import DetailView from '../../client/src/views/DetailView.vue'
import { useSearchStore, mapCombo } from '../../client/src/store'
import { makeCombo, makeTravel } from '../fixtures/combos'

let pinia

beforeEach(() => {
  pinia = createPinia()
  setActivePinia(pinia)
})

function mountDetail(combo, id) {
  const store = useSearchStore()
  const mapped = mapCombo(combo ?? makeCombo(), { radiusKm: 5 })
  store.results = [mapped]
  store.status = 'ok'
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/results', component: { template: '<div />' } }
    ]
  })
  const wrapper = mount(DetailView, {
    props: { id: id ?? mapped.id },
    global: { plugins: [pinia, router] }
  })
  return { wrapper, store, mapped }
}

describe('AC-3.2.1 — Each card carries the verified facts', () => {
  it('TC-3.2.1-01 — the detail page shows name, category, distance and the weather, UV and air facts', () => {
    const { wrapper, mapped } = mountDetail()
    expect(wrapper.find('h1').text()).toBe(mapped.name)
    expect(wrapper.find('.eyebrow').text()).toContain(mapped.categoryLabel)
    expect(wrapper.find('.eyebrow').text()).toMatch(/[\d.]+ km away/)
    expect(wrapper.findAll('.fact')).toHaveLength(3)
    // labels sit under the values, with no extra line above
    const tiles = wrapper.findAll('.fact')
    expect(tiles[0].find('svg.sun').exists()).toBe(true)
    expect(tiles[1].text()).toMatch(/UV index$/)
    expect(tiles[2].text()).toMatch(/Air quality$/)
    expect(tiles[1].find('.fact-label').text()).toBe('UV index')
    expect(wrapper.find('.facts').text()).not.toMatch(/☀|≋/)
  })

  it('TC-3.2.1-01 — the matched bucket and entered duration are both shown, excluding travel', () => {
    const { wrapper } = mountDetail()
    expect(wrapper.find('.walk-plan').text()).toMatch(/40 of your 45 min to play/)
  })
})

describe('Place page design', () => {
  it('shows the Play list map style as a hero, with a back button and the temperature over it', async () => {
    const { wrapper, store } = mountDetail()
    store.context = { available: true, temp_c: 16, precip_prob: 0.1, uv_index: 4, pm25: 8 }
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.hero .place-map').exists()).toBe(true)
    expect(wrapper.find('.hero .round-btn').exists()).toBe(true)
    expect(wrapper.find('.hero .temp-pill').text()).toContain('°')
  })

  it('has a Go link for directions and a Pick a mission section with Shuffle and a Start pill', () => {
    const { wrapper } = mountDetail()
    expect(wrapper.find('.go-btn').text()).toMatch(/Go/)
    expect(wrapper.find('.missions-head h2').text()).toBe('Pick a mission')
    expect(wrapper.find('.shuffle').exists()).toBe(true)
    expect(wrapper.find('.start').exists()).toBe(true)
  })
})

describe('Trip row', () => {
  it('shows the server travel time and the mode chosen on Start, and no id or fit pill', async () => {
    const store = useSearchStore()
    store.travelMode = 'driving'
    const { wrapper } = mountDetail(makeCombo({ travel: makeTravel({ mode: 'driving', out_min: 7, source: 'estimate' }) }))
    expect(wrapper.find('.walk-text').text()).toMatch(/^7 min drive/)
    expect(wrapper.find('.walk-icon path').attributes('d')).toMatch(/^M5 16.5/) // car icon
    expect(wrapper.find('.eyebrow').text()).not.toMatch(/#/)
    expect(wrapper.find('.eyebrow-row').exists()).toBe(false)
    expect(wrapper.text()).not.toMatch(/good fit|rain risk/i)
  })

  it('says walk with a walking time when Start chose walking', () => {
    const { wrapper } = mountDetail(makeCombo({ travel: makeTravel({ mode: 'walking', out_min: 6, source: 'openrouteservice' }) }))
    expect(wrapper.find('.walk-text').text()).toMatch(/^6 min walk/)
  })

  it('does not show a travel time worked out for a different mode; it estimates for the chosen one', () => {
    const store = useSearchStore()
    store.travelMode = 'driving'
    const { wrapper } = mountDetail(makeCombo({ travel: makeTravel({ mode: 'walking', out_min: 6 }) }))
    // 0.4 km: 1.3 x 0.4 / 30 km/h is just over 1 min, plus 5 to park, rounded up
    expect(wrapper.find('.walk-text').text()).toMatch(/^7 min drive/)
  })
})

describe('AC-3.2.2 — Unverified facts stay off the card', () => {
  it('TC-3.2.2-01 — the streamlined page makes no hours, cost or accessibility claims', () => {
    const { wrapper } = mountDetail()
    expect(wrapper.text()).not.toMatch(/open(s|ing)? at|opening hours|\$|entry fee|accessibility/i)
  })
})


describe('Guard rails', () => {
  it('an unknown place id shows a not-found state instead of a broken page', () => {
    const { wrapper } = mountDetail(undefined, 'no-such-place')
    expect(wrapper.text()).toContain('Place not found.')
  })
})
