// Iteration 2, F20 — unit tests for client/src/historyStore.js.

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useHistoryStore, feedbackEmoji, feedbackLabel, relativeDayLabel } from '../../client/src/historyStore'

beforeEach(() => {
  setActivePinia(createPinia())
})

afterEach(() => {
  vi.useRealTimers()
})

function iso(d) {
  return d.toISOString().slice(0, 10)
}

describe('F20 — history store', () => {
  it('starts empty with no most-recent record', () => {
    const store = useHistoryStore()
    expect(store.records).toEqual([])
    expect(store.mostRecent).toBeNull()
    expect(store.thisWeekCount).toBe(0)
    expect(store.lastWeekCount).toBe(0)
  })

  it('addRecord puts the newest record first', () => {
    const store = useHistoryStore()
    store.addRecord({ date: iso(new Date()), placeName: 'A' })
    store.addRecord({ date: iso(new Date()), placeName: 'B' })
    expect(store.records.map((r) => r.placeName)).toEqual(['B', 'A'])
    expect(store.mostRecent.placeName).toBe('B')
  })

  it('counts this-week and last-week records against a fixed Wednesday', () => {
    // Wed 2026-09-16: this week is Mon 09-14 .. Sun 09-20, last week Mon 09-07 .. Sun 09-13
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-16T12:00:00'))
    const store = useHistoryStore()
    store.addRecord({ date: '2026-09-14' }) // this week (Monday)
    store.addRecord({ date: '2026-09-20' }) // this week (Sunday)
    store.addRecord({ date: '2026-09-07' }) // last week (Monday)
    store.addRecord({ date: '2026-09-13' }) // last week (Sunday)
    store.addRecord({ date: '2026-09-21' }) // next week — neither
    expect(store.thisWeekCount).toBe(2)
    expect(store.lastWeekCount).toBe(2)
  })

  it('byDate groups records by their date', () => {
    const store = useHistoryStore()
    store.addRecord({ date: '2026-09-14', placeName: 'A' })
    store.addRecord({ date: '2026-09-14', placeName: 'B' })
    store.addRecord({ date: '2026-09-15', placeName: 'C' })
    expect(store.byDate['2026-09-14']).toHaveLength(2)
    expect(store.byDate['2026-09-15']).toHaveLength(1)
  })
})

describe('F20 — feedback helpers', () => {
  it('map every option id to its label and emoji', () => {
    expect(feedbackLabel('fun')).toBe('Fun')
    expect(feedbackEmoji('fun')).toBe('🙂')
    expect(feedbackLabel('too_hard')).toBe('Too hard')
  })

  it('return empty strings for an unknown id', () => {
    expect(feedbackLabel('nope')).toBe('')
    expect(feedbackEmoji('nope')).toBe('')
  })
})

describe('F20 — relativeDayLabel', () => {
  it('labels today, yesterday, and falls back to the weekday name', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-16T18:00:00')) // a Wednesday
    expect(relativeDayLabel('2026-09-16')).toBe('Today')
    expect(relativeDayLabel('2026-09-15')).toBe('Yesterday')
    expect(relativeDayLabel('2026-09-14')).toBe('Monday')
  })
})
