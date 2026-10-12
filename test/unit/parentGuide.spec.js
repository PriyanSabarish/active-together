// Story 9.2 — the parent guide for at-home activities, shown on the run screen.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('../../client/src/api', () => ({ postVerifyStep: vi.fn(), postMissions: vi.fn(), postHomeMissions: vi.fn() }))
vi.mock('../../client/src/figures', () => ({
  loadFigure: vi.fn(() => Promise.resolve('')),
  cachedFigure: vi.fn(() => ''),
  preloadFigures: vi.fn()
}))

import MissionRunView from '../../client/src/views/MissionRunView.vue'
import { useMissionStore } from '../../client/src/missionStore'
import { PARENT_GUIDES, guideFor } from '../../client/src/parentGuides'

const mission = (templateId, steps = 5) => ({
  id: 'm1',
  templateId,
  title: 'Home: Test',
  placeName: 'Home',
  category: 'home',
  ageBand: '8-10',
  durationMin: 40,
  equipment: '',
  steps: Array.from({ length: steps }, (_, i) => ({ title: `Step ${i + 1}`, confirm: 'tap', icon: 'sun', figure: null }))
})

function mountRun(m) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useMissionStore()
  store.candidates = [m]
  store.chooseMission(m.id)
  store.startMission()
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: MissionRunView }, { path: '/play/finished', component: { template: '<div />' } }] })
  return { wrapper: mount(MissionRunView, { global: { plugins: [pinia, router] } }), store }
}

beforeEach(() => setActivePinia(createPinia()))

describe('guide content', () => {
  it('covers all three home templates with five stages each, and every band for each stage', () => {
    expect(Object.keys(PARENT_GUIDES).sort()).toEqual([
      'activity_home_missing_power_crystals',
      'activity_home_secret_agent_escape',
      'activity_home_sock_ball_carnival'
    ])
    for (const g of Object.values(PARENT_GUIDES)) {
      expect(g.stages).toHaveLength(5)
      expect(g.setup.length).toBeGreaterThan(0)
      expect(g.kit.length).toBeGreaterThan(0)
      expect(g.setupTime).toMatch(/min/)
      for (const stage of g.stages) expect(stage.parts.length).toBeGreaterThan(0)
    }
  })

  it('has no guide for an outdoor template', () => {
    expect(guideFor('activity_colour_hunt')).toBeNull()
  })
})

describe('run screen', () => {
  it('opens the guide on the first task of a home mission, with the age band note and setup', async () => {
    const { wrapper } = mountRun(mission('activity_home_secret_agent_escape'))
    const sheet = wrapper.find('[aria-label="Parent guide"]')
    expect(sheet.exists()).toBe(true)
    expect(sheet.text()).toMatch(/Recover the badge/)
    expect(sheet.text()).toMatch(/Ages 8–10/)
    expect(sheet.text()).toMatch(/Before you start/)
    expect(sheet.text()).toMatch(/You.ll need/)
    expect(sheet.text()).toMatch(/Say first/)
  })

  it('collapses setup after the first task and expands safety rules on tap', async () => {
    const { wrapper, store } = mountRun(mission('activity_home_sock_ball_carnival'))
    await wrapper.find('.close').trigger('click')
    store.stepIndex = 1
    await wrapper.vm.$nextTick()
    await wrapper.find('.run-guide').trigger('click')
    const sheet = wrapper.find('[aria-label="Parent guide"]')
    expect(sheet.text()).not.toMatch(/Say first/)
    expect(sheet.text()).not.toMatch(/Do not climb or jump on furniture/)
    await sheet.findAll('.acc-head')[1].trigger('click')
    expect(sheet.text()).toMatch(/Do not climb or jump on furniture/)
  })

  it('can be closed and reopened from the Parent guide button', async () => {
    const { wrapper } = mountRun(mission('activity_home_sock_ball_carnival'))
    await wrapper.find('.close').trigger('click')
    expect(wrapper.find('[aria-label="Parent guide"]').exists()).toBe(false)
    await wrapper.find('.run-guide').trigger('click')
    expect(wrapper.find('[aria-label="Parent guide"]').exists()).toBe(true)
  })

  it('follows the current task', async () => {
    const { wrapper, store } = mountRun(mission('activity_home_sock_ball_carnival'))
    await wrapper.find('.close').trigger('click')
    store.stepIndex = 1
    await wrapper.vm.$nextTick()
    await wrapper.find('.run-guide').trigger('click')
    expect(wrapper.find('[aria-label="Parent guide"]').text()).toMatch(/Sock bowling/)
  })

  it('does not appear on an outdoor mission', async () => {
    const { wrapper } = mountRun(mission('activity_colour_hunt'))
    expect(wrapper.find('.run-guide').exists()).toBe(false)
    expect(wrapper.find('[aria-label="Parent guide"]').exists()).toBe(false)
  })
})
