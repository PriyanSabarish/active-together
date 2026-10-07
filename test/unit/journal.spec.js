// Iteration 3 — mission photos and journal helpers: runId and per-step
// results on the mission store, photoStore linking/deletion (D11, D15), and
// the Week/You helpers (kindOf, weekStreak, localIso).

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMissionStore, MOCK_MISSIONS } from '../../client/src/missionStore'
import { usePhotoStore } from '../../client/src/photoStore'
import { kindOf, weekStreak, localIso } from '../../client/src/historyStore'

beforeEach(() => {
  setActivePinia(createPinia())
})

function running() {
  const store = useMissionStore()
  store.candidates = [...MOCK_MISSIONS]
  store.chooseMission('bark-detective')
  store.startMission()
  return store
}

describe('mission run — runId and step results', () => {
  it('startMission creates a fresh runId each run', () => {
    const store = running()
    const first = store.runId
    expect(first).toBeTruthy()
    store.resetMission()
    expect(store.runId).toBeNull()
    store.candidates = [...MOCK_MISSIONS]
    store.chooseMission('bark-detective')
    store.startMission()
    expect(store.runId).not.toBe(first)
  })

  it('completeStep records done or skipped and finishes on the last step', () => {
    const store = running()
    store.completeStep('done')
    store.completeStep('skipped')
    expect(store.results).toEqual({ 0: 'done', 1: 'skipped' })
    store.completeStep('done')
    expect(store.status).toBe('done')
  })

  it('goToStep jumps within range only', () => {
    const store = running()
    store.goToStep(2)
    expect(store.stepIndex).toBe(2)
    store.goToStep(9)
    expect(store.stepIndex).toBe(2)
  })
})

describe('photoStore', () => {
  it('links photos to a run and removeRun deletes them all (D11)', () => {
    const photos = usePhotoStore()
    photos.addPhoto({ runId: 'a', url: 'data:,1', stepIndex: 0 })
    photos.addPhoto({ runId: 'a', url: 'data:,2', source: 'end' })
    photos.addPhoto({ runId: 'b', url: 'data:,3' })
    expect(photos.countForRun('a')).toBe(2)
    photos.removeRun('a')
    expect(photos.countForRun('a')).toBe(0)
    expect(photos.countForRun('b')).toBe(1)
  })

  it('removePhoto can be undone from the toast', () => {
    vi.useFakeTimers()
    const photos = usePhotoStore()
    const p = photos.addPhoto({ runId: 'a', url: 'data:,1' })
    photos.removePhoto(p.id)
    expect(photos.photos).toHaveLength(0)
    expect(photos.toast.text).toBe('Photo deleted')
    photos.undoToast()
    expect(photos.photos.map((x) => x.id)).toEqual([p.id])
    expect(photos.toast).toBeNull()
    vi.useRealTimers()
  })
})

describe('journal helpers', () => {
  it('kindOf sorts outings into park, exploring and at home', () => {
    expect(kindOf({ category: 'home', placeName: 'Home' })).toBe('home')
    expect(kindOf({ category: 'trail_access', placeName: 'Jells Park' })).toBe('exploring')
    expect(kindOf({ category: 'playground', placeName: 'Napier Park' })).toBe('park')
  })

  it('weekStreak counts consecutive weeks and restarts after a gap', () => {
    const now = new Date(2026, 9, 7) // Wed 7 Oct 2026
    const at = (y, m, d) => ({ date: localIso(new Date(y, m, d)) })
    expect(weekStreak([at(2026, 9, 5), at(2026, 8, 30), at(2026, 8, 22)], now)).toBe(3)
    expect(weekStreak([at(2026, 9, 5), at(2026, 8, 22)], now)).toBe(1)
    // Nothing yet this week: counting starts from last week.
    expect(weekStreak([at(2026, 8, 30), at(2026, 8, 22)], now)).toBe(2)
    expect(weekStreak([], now)).toBe(0)
  })

  it('localIso uses the local calendar day', () => {
    expect(localIso(new Date(2026, 9, 5, 0, 30))).toBe('2026-10-05')
  })
})
