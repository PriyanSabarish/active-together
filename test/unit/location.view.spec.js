// Iteration 1 — component tests for LocationView (AC-1.1.1, AC-1.1.2).

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({
  postRecommendations: vi.fn(),
  postHomeMissions: vi.fn(),
  getContext: vi.fn(),
  getHourlyForecast: vi.fn(() => Promise.resolve([])),
  searchAddresses: vi.fn()
}))

import LocationView from '../../client/src/views/LocationView.vue'
import { useSearchStore } from '../../client/src/store'
import { usePreferencesStore } from '../../client/src/preferencesStore'
import { searchAddresses, postHomeMissions } from '../../client/src/api'

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

describe('Travel spread toggle', () => {
  it('the label reads "Up to ..." and the toggle switches ranking mode', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    await wrapper.findAll('.travel-btn')[5].trigger('click')
    // The "How long to play?" step now comes first and shows its own .big line.
    const far = wrapper.findAll('.big').find((b) => b.text().startsWith('Up to'))
    expect(far.text()).toMatch(/^Up to 30\s*min walk, each way/)
    const buttons = wrapper.findAll('.rank-btn')
    expect(buttons.map((b) => b.text())).toEqual(['Mix it up', 'Nearest first'])
    expect(store.rankingMode).toBe('spread')
    await buttons[1].trigger('click')
    expect(store.rankingMode).toBe('nearest')
    await buttons[0].trigger('click')
    expect(store.rankingMode).toBe('spread')
  })
})

describe('Your kid sheet', () => {
  async function openKid(setting) {
    const wrapper = mountView()
    useSearchStore().setting = setting
    await wrapper.vm.$nextTick()
    await wrapper.find('.kid-row').trigger('click')
    return wrapper
  }

  it('shows the age band and the outdoor likes for Outdoors', async () => {
    const wrapper = await openKid('outdoor')
    const sheet = wrapper.find('[aria-label="Your kid"]')
    expect(sheet.exists()).toBe(true)
    expect(sheet.text()).toContain('Age')
    expect(sheet.text()).toContain('Likes')
    expect(sheet.text()).toContain('Playground')
  })

  it('shows the kinds of indoor place to like for Indoor place, not the outdoor categories', async () => {
    const wrapper = await openKid('indoor_place')
    const sheet = wrapper.find('[aria-label="Your kid"]')
    expect(sheet.text()).toContain('Age')
    expect(sheet.text()).toContain('Likes')
    for (const kind of ['Swimming', 'Recreation centre', 'Indoor sports', 'Clubs']) expect(sheet.text()).toContain(kind)
    expect(sheet.text()).not.toContain('Playground')
    expect(sheet.findAll('.like')).toHaveLength(4)
  })

  it('saves indoor choices apart from the outdoor ones', async () => {
    const wrapper = await openKid('indoor_place')
    const prefs = usePreferencesStore()
    const row = wrapper.findAll('.like').find((r) => r.text().includes('Clubs'))
    await row.find('.tri-btn.nope').trigger('click')
    await wrapper.find('.save').trigger('click')
    expect(prefs.excludedIndoorKinds).toEqual(['clubs'])
    expect(prefs.excludedCategories).toEqual([])
  })

  it('shows only the age band for At home, with no likes', async () => {
    const wrapper = await openKid('home')
    const sheet = wrapper.find('[aria-label="Your kid"]')
    expect(sheet.text()).toContain('Age')
    expect(sheet.text()).not.toContain('Likes')
    expect(sheet.find('.clear').exists()).toBe(false)
  })
})

describe('Start header on scroll', () => {
  it('is a plain bar at the top and floats as a pill once the page has scrolled', async () => {
    const wrapper = mountView()
    expect(wrapper.find('.app-header').classes()).not.toContain('floating')
    const area = wrapper.find('.scroll-area.start')
    area.element.scrollTop = 40
    await area.trigger('scroll')
    expect(wrapper.find('.app-header').classes()).toContain('floating')
    expect(wrapper.find('.app-header').classes()).toContain('overlay')
    area.element.scrollTop = 0
    await area.trigger('scroll')
    expect(wrapper.find('.app-header').classes()).not.toContain('floating')
  })
})

describe('Story 9.1 — Outdoors / At home / Indoor place', () => {
  it('At home hides the location steps and needs a mission instead of a place', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    postHomeMissions.mockResolvedValue({
      missions: [1, 2, 3].map((n) => ({
        mission_id: 'm' + n, template_id: 'activity_home_' + n, title: 'Home ' + n, age_band: '8-10', estimated_minutes: 40,
        equipment: [], steps: [{ sequence: 1, prompt_text: 'Go.', verify_mode: 'self', prompt_id: null }]
      }))
    })
    store.setting = 'home'
    await flushPromises()
    expect(postHomeMissions).toHaveBeenCalledWith({ durationMin: store.stayMin, ageBand: '8-10', recentTemplateIds: [] })
    expect(wrapper.findAll('.home-item')).toHaveLength(3)
    expect(wrapper.find('button.use-location').exists()).toBe(false)
    expect(wrapper.find('.travel-btn').exists()).toBe(false)
    const cta = wrapper.find('.btn-primary')
    expect(cta.attributes('disabled')).toBeDefined()
    await wrapper.find('.home-item').trigger('click')
    expect(cta.attributes('disabled')).toBeUndefined()
    expect(cta.text()).toMatch(/^Play /)
  })

  it('At home: each activity has a Guide link that opens the setup and rules before play', async () => {
    const wrapper = mountView()
    const store = useSearchStore()
    postHomeMissions.mockResolvedValue({
      missions: [
        { mission_id: 'a', template_id: 'activity_home_missing_power_crystals', title: 'Home: Crystals', parent_guide: { rules: ['Walk indoors.'], setupTime: '5–10 min', kit: ['Socks'], setup: ['Draw a map.'], opening: 'Captain, go.', stages: [{ title: 'S1', parts: [{ do: ['x'] }] }] }, age_band: '8-10', estimated_minutes: 20, equipment: [], steps: [{ sequence: 1, prompt_text: 'Go.', verify_mode: 'self', prompt_id: null }] },
        { mission_id: 'b', template_id: 'activity_not_home', title: 'No guide', age_band: '8-10', estimated_minutes: 20, equipment: [], steps: [{ sequence: 1, prompt_text: 'Go.', verify_mode: 'self', prompt_id: null }] }
      ]
    })
    store.setting = 'home'
    await flushPromises()
    const links = wrapper.findAll('.home-guide')
    expect(links).toHaveLength(1) // only the activity that has a guide
    await links[0].trigger('click')
    const sheet = wrapper.find('[aria-label="Parent guide"]')
    expect(sheet.exists()).toBe(true)
    expect(sheet.text()).toMatch(/Before you start/)
    expect(sheet.text()).toMatch(/Say first/)
    expect(sheet.text()).not.toMatch(/Task 1/)
    // opening the guide does not pick the activity
    expect(wrapper.find('.btn-primary').attributes('disabled')).toBeDefined()
    await sheet.find('.close').trigger('click')
    expect(wrapper.find('[aria-label="Parent guide"]').exists()).toBe(false)
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
