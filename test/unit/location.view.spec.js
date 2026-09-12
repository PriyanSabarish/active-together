// Iteration 1 — component tests for LocationView (AC-1.1.1, AC-1.1.2).

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  getContext: vi.fn(),
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

describe('AC-1.1.2 — Radius options', () => {
  it('TC-1.1.2-01 — only 3 km, 5 km and 10 km can be selected', () => {
    const wrapper = mountView()
    const btns = wrapper.findAll('.radius-btn')
    expect(btns.map((b) => b.text())).toEqual(['3 km', '5 km', '10 km'])
  })

  it('TC-1.1.2-01 — the selected radius is applied to the store used by the search', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    await wrapper.findAll('.radius-btn')[2].trigger('click')
    expect(store.radiusKm).toBe(10)
    await wrapper.findAll('.radius-btn')[0].trigger('click')
    expect(store.radiusKm).toBe(3)
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
