// Iteration 2, F14 — unit tests for client/src/missionStore.js.
// No UI reads this store yet; these tests exist so the shape F15-F18 will be
// built against is verified before three screens depend on it.

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMissionStore, MOCK_MISSIONS } from '../../client/src/missionStore'

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('F14 — mission store on mock data', () => {
  it('starts with no active mission and the mock candidates offered', () => {
    const store = useMissionStore()
    expect(store.active).toBeNull()
    expect(store.status).toBe('not_started')
    expect(store.candidates).toHaveLength(MOCK_MISSIONS.length)
    expect(store.stepStates).toEqual([])
  })

  it('chooseMission sets the active mission and resets progress', () => {
    const store = useMissionStore()
    store.chooseMission('bark-detective')
    expect(store.active?.id).toBe('bark-detective')
    expect(store.stepIndex).toBe(0)
    expect(store.status).toBe('not_started')
    expect(store.totalSteps).toBe(3)
  })

  it('an unknown mission id leaves the store unchanged', () => {
    const store = useMissionStore()
    store.chooseMission('does-not-exist')
    expect(store.active).toBeNull()
  })

  it('startMission moves to in_progress at the first step', () => {
    const store = useMissionStore()
    store.chooseMission('shadow-tag')
    store.startMission()
    expect(store.status).toBe('in_progress')
    expect(store.currentStep).toEqual(store.active.steps[0])
    expect(store.stepStates).toEqual(['active', 'todo'])
  })

  it('advanceStep moves through steps and finishes on the last one', () => {
    const store = useMissionStore()
    store.chooseMission('shadow-tag') // two steps
    store.startMission()

    store.advanceStep()
    expect(store.status).toBe('in_progress')
    expect(store.stepIndex).toBe(1)
    expect(store.stepStates).toEqual(['done', 'active'])

    store.advanceStep()
    expect(store.status).toBe('done')
    // stepIndex stays put; every step reads as done once the mission is finished
    expect(store.stepStates).toEqual(['done', 'done'])
  })

  it('advanceStep before startMission is a no-op', () => {
    const store = useMissionStore()
    store.chooseMission('bark-detective')
    store.advanceStep()
    expect(store.status).toBe('not_started')
    expect(store.stepIndex).toBe(0)
  })

  it('resetMission clears the active mission entirely', () => {
    const store = useMissionStore()
    store.chooseMission('bark-detective')
    store.startMission()
    store.advanceStep()
    store.resetMission()
    expect(store.active).toBeNull()
    expect(store.stepIndex).toBe(0)
    expect(store.status).toBe('not_started')
  })
})
