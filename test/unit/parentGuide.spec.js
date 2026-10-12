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
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// The guide text is served by the backend with each home mission; this is its source file.
const SOURCE = JSON.parse(fs.readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../server/content/missions/home_parent_guides.json'), 'utf8'))
const PARENT_GUIDES = SOURCE.guides
const withRules = (g) => ({ rules: SOURCE.rules, ...g })

const mission = (templateId, steps = 5) => ({
  id: 'm1',
  templateId,
  guide: PARENT_GUIDES[templateId] ? withRules(PARENT_GUIDES[templateId]) : null,
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

describe('guide content (served by the backend)', () => {
  it('covers all three home templates with five stages each', () => {
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
    }
    expect(SOURCE.rules.length).toBeGreaterThan(0)
  })

  it('a mapped mission carries the guide the server sent, and none when it sent none', async () => {
    const { mapMission } = await import('../../client/src/missionStore')
    const base = { mission_id: 'a', template_id: 't', title: 'T', age_band: '8-10', estimated_minutes: 20, steps: [] }
    expect(mapMission({ ...base, parent_guide: { rules: ['r'] } }, { placeName: 'Home', category: 'home', reason: '' }).guide).toEqual({ rules: ['r'] })
    expect(mapMission(base, { placeName: 'Home', category: 'home', reason: '' }).guide).toBeNull()
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
