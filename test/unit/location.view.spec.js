// Iteration 1 — component tests for LocationView (AC-1.1.1, AC-1.1.2).

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  getContext: vi.fn(),
  getHourlyForecast: vi.fn(() => Promise.resolve([])),
  searchAddresses: vi.fn()
}))

import LocationView from '../../client/src/views/LocationView.vue'
import { useSearchStore } from '../../client/src/store'
import { searchAddresses } from '../../client/src/api'

let pinia
let geoMock

beforeEach(() => {
  pinia = createPinia()
  setActivePinia(pinia)
  geoMock = { getCurrentPosition: vi.fn() }
  Object.defineProperty(navigator, 'geolocation', {
    value: geoMock,
    configurable: true
  })
  searchAddresses.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
  delete navigator.geolocation
})

function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: LocationView },
      { path: '/time', component: { template: '<div />' } }
    ]
  })
  return mount(LocationView, { global: { plugins: [pinia, router] } })
}

describe('AC-1.1.1 — Current or manual location', () => {
  it('TC-1.1.1-01 — geolocation is requested only on demand, not on page load', async () => {
    const wrapper = mountView()
    expect(geoMock.getCurrentPosition).not.toHaveBeenCalled()

    await wrapper.find('button.use-location').trigger('click')
    expect(geoMock.getCurrentPosition).toHaveBeenCalledTimes(1)
  })

  it('TC-1.1.1-01 — a granted position is stored as the search point', async () => {
    geoMock.getCurrentPosition.mockImplementation((ok) =>
      ok({ coords: { latitude: -37.9, longitude: 145.1 } })
    )
    const wrapper = mountView()
    const store = useSearchStore()
    await wrapper.find('button.use-location').trigger('click')
    expect(store.useMyLocation).toBe(true)
    expect(store.myLocation).toEqual({ latitude: -37.9, longitude: 145.1 })
  })

  it('TC-1.1.1-02 — permission denial is handled and address entry keeps working', async () => {
    geoMock.getCurrentPosition.mockImplementation((_ok, fail) =>
      fail({ code: 1, PERMISSION_DENIED: 1 })
    )
    const wrapper = mountView()
    const store = useSearchStore()

    await wrapper.find('button.use-location').trigger('click')
    expect(store.useMyLocation).toBe(false)
    expect(wrapper.text()).toMatch(/permission was denied.*Enter an address/i)

    searchAddresses.mockResolvedValue({ suggestions: [{
      id: '123', label: '1 Centre Road Clayton Vic 3168',
      latitude: -37.927, longitude: 145.12, suburb: 'Clayton', postcode: '3168'
    }] })
    vi.useFakeTimers()
    const input = wrapper.find('input[type="text"]')
    await input.setValue('1 Centre Road Clayton')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.find('.suggest-item').trigger('click')
    vi.useRealTimers()
    expect(store.selectedAddress.label).toMatch(/Centre Road/)
    expect(store.hasLocation).toBe(true)
  })

  it('TC-1.1.1-02 — a browser without geolocation still allows manual entry', async () => {
    delete navigator.geolocation
    const wrapper = mountView()
    await wrapper.find('button.use-location').trigger('click')
    expect(wrapper.text()).toMatch(/not available in this browser.*Enter an address/i)
  })
})

describe('AC-1.1.2 — Radius options (chosen as travel minutes)', () => {
  it('TC-1.1.2-01 — how far is picked as 5-30 minutes each way, walking or driving', () => {
    const wrapper = mountView()
    expect(wrapper.findAll('.travel-btn').map((b) => b.text())).toEqual(['5', '10', '15', '20', '25', '30'])
    expect(wrapper.findAll('.mode').map((b) => b.text())).toEqual(['Walk', 'Drive'])
  })

  it('TC-1.1.2-01 — travel minutes map onto the backend\'s 3, 5 or 10 km radius only', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    await wrapper.findAll('.travel-btn')[5].trigger('click') // walk 30 min ~ 2.5 km
    expect(store.radiusKm).toBe(3)
    await wrapper.findAll('.mode')[1].trigger('click') // drive 30 min ~ 15 km, capped
    expect(store.radiusKm).toBe(10)
    await wrapper.findAll('.travel-btn')[1].trigger('click') // drive 10 min ~ 5 km
    expect(store.radiusKm).toBe(5)
    expect([3, 5, 10]).toContain(store.radiusKm)
  })
})

describe('Story 9.1 — Outdoors / At home / Indoor place', () => {
  it('At home hides the location steps and needs a mission instead of a place', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    store.setting = 'home'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('button.use-location').exists()).toBe(false)
    expect(wrapper.find('.travel-btn').exists()).toBe(false)
    const cta = wrapper.find('.btn-primary')
    expect(cta.attributes('disabled')).toBeDefined()
    await wrapper.find('.home-item:not([disabled])').trigger('click')
    expect(cta.attributes('disabled')).toBeUndefined()
    expect(cta.text()).toMatch(/^Play /)
  })

  it('Indoor place keeps where-from and how far, drops when and time there', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    store.setting = 'indoor_place'
    await wrapper.vm.$nextTick()
    expect(wrapper.find('button.use-location').exists()).toBe(true)
    expect(wrapper.find('.travel-btn').exists()).toBe(true)
    expect(wrapper.find('.stay-btn').exists()).toBe(false)
    expect(wrapper.find('.strip').exists()).toBe(false)
  })
})

describe('Guard rails', () => {
  it('Next stays disabled until a valid location is chosen', async () => {
    const wrapper = mountView()
    const next = wrapper.find('.btn-primary')
    expect(next.attributes('disabled')).toBeDefined()
    searchAddresses.mockResolvedValue({ suggestions: [{
      id: '123', label: '1 Centre Road Clayton Vic 3168',
      latitude: -37.927, longitude: 145.12, suburb: 'Clayton', postcode: '3168'
    }] })
    vi.useFakeTimers()
    await wrapper.find('input[type="text"]').setValue('1 Centre Road')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.find('.suggest-item').trigger('click')
    vi.useRealTimers()
    expect(next.attributes('disabled')).toBeUndefined()
  })
})
