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
import { makeCombo } from '../fixtures/combos'

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
  it('TC-3.2.1-01 — the detail page shows name, category, distance and conditions', () => {
    const { wrapper, mapped } = mountDetail()
    expect(wrapper.find('h1').text()).toBe(mapped.name)
    expect(wrapper.find('.subtitle').text()).toContain(mapped.categoryLabel)
    expect(wrapper.find('.subtitle').text()).toMatch(/[\d.]+ km away/)
    expect(wrapper.findAll('.condition-row')).toHaveLength(mapped.conditions.length)
  })

  it('TC-3.2.1-01 — the matched bucket and entered duration are both shown, excluding travel', () => {
    const { wrapper } = mountDetail()
    expect(wrapper.find('.duration-main').text()).toMatch(/40-minute on-site plan/)
    expect(wrapper.find('.duration-sub').text()).toMatch(/45-min request · excludes travel/)
  })
})

describe('AC-3.2.2 — Unverified facts stay off the card', () => {
  it('TC-3.2.2-01 — the page shows the candidate disclaimer and no hours/cost claims', () => {
    const { wrapper } = mountDetail()
    expect(wrapper.find('.disclaimer').text()).toMatch(/opening hours, cost and accessibility aren't available yet/i)
    expect(wrapper.find('.expect').text()).toMatch(/Not verified/i)
    expect(wrapper.text()).not.toMatch(/open(s|ing)? at|\$|entry fee/i)
  })
})

describe('AC-3.3.1 — The explanation uses only decision inputs', () => {
  it('TC-3.3.1-01 — the backend explanation and reasons are rendered verbatim', () => {
    const { wrapper, mapped } = mountDetail()
    expect(wrapper.find('.explanation').text()).toBe(mapped.reason)
    expect(wrapper.findAll('.why-list li').map((li) => li.text())).toEqual(mapped.reasons)
  })
})

describe('Guard rails', () => {
  it('an unknown place id shows a not-found state instead of a broken page', () => {
    const { wrapper } = mountDetail(undefined, 'no-such-place')
    expect(wrapper.text()).toContain('Place not found.')
  })
})
