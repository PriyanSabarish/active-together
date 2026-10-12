// Story 9.2 — at-home missions come from POST /recommendations (setting home).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('../../client/src/api', () => ({
  postMissions: vi.fn(),
  postHomeMissions: vi.fn()
}))

import { postHomeMissions } from '../../client/src/api'
import { useMissionStore } from '../../client/src/missionStore'

const serverMission = (id, title) => ({
  mission_id: id,
  template_id: `activity_home_${id}`,
  title,
  age_band: '8-10',
  estimated_minutes: 20,
  equipment: ['rolled socks'],
  place_name: 'Home',
  place_id: null,
  steps: [
    { sequence: 1, prompt_text: 'Roll a sock.', verify_mode: 'self', prompt_id: null, figure: 'fig_1' },
    { sequence: 2, prompt_text: 'Toss it.', verify_mode: 'self', prompt_id: null }
  ]
})

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('fetchHomeMissions', () => {
  it('TC-9.2-01 — maps the server missions into the shape the screens use, placed at Home', async () => {
    postHomeMissions.mockResolvedValue({ missions: [serverMission('a', 'Sock Ball'), serverMission('b', 'Crystals')] })
    const store = useMissionStore()
    await store.fetchHomeMissions({ durationMin: 20, ageBand: '8-10' })
    expect(postHomeMissions).toHaveBeenCalledWith({ durationMin: 20, ageBand: '8-10', recentTemplateIds: [] })
    expect(store.homeMissions).toHaveLength(2)
    expect(store.homeMissions[0]).toMatchObject({ id: 'a', title: 'Sock Ball', placeName: 'Home', category: 'home', durationMin: 20 })
    expect(store.homeMissions[0].steps[0]).toMatchObject({ title: 'Roll a sock.', confirm: 'tap', figure: 'fig_1' })
    expect(store.homeLoading).toBe(false)
  })

  it('TC-9.2-02 — a failed request sets an error and clears the list', async () => {
    postHomeMissions.mockRejectedValue(new Error('Could not reach the service.'))
    const store = useMissionStore()
    await store.fetchHomeMissions({ durationMin: 20, ageBand: '8-10' })
    expect(store.homeMissions).toEqual([])
    expect(store.homeError).toMatch(/Could not reach/)
  })

  it('TC-9.2-03 — only the newest request is kept when two overlap', async () => {
    let release
    postHomeMissions.mockImplementationOnce(() => new Promise((r) => { release = r }))
    postHomeMissions.mockResolvedValueOnce({ missions: [serverMission('new', 'New')] })
    const store = useMissionStore()
    const first = store.fetchHomeMissions({ durationMin: 20, ageBand: '8-10' })
    await store.fetchHomeMissions({ durationMin: 40, ageBand: '8-10' })
    release({ missions: [serverMission('old', 'Old')] })
    await first
    expect(store.homeMissions.map((m) => m.id)).toEqual(['new'])
  })

  it('TC-9.2-04 — startHomeMission starts the chosen server mission', async () => {
    postHomeMissions.mockResolvedValue({ missions: [serverMission('a', 'Sock Ball')] })
    const store = useMissionStore()
    await store.fetchHomeMissions({ durationMin: 20, ageBand: '8-10' })
    store.startHomeMission('a')
    expect(store.active.title).toBe('Sock Ball')
    expect(store.status).toBe('in_progress')
  })
})
