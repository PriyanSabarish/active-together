// Iteration 2, F10 — unit tests for client/src/preferencesStore.js.

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePreferencesStore, AGE_BANDS } from '../../client/src/preferencesStore'
import { CATEGORY_META } from '../../client/src/store'

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('F10 — preferences store', () => {
  it('defaults every category to a neutral affinity and age band 6-8', () => {
    const store = usePreferencesStore()
    expect(Object.keys(store.affinities).sort()).toEqual(Object.keys(CATEGORY_META).sort())
    for (const v of Object.values(store.affinities)) expect(v).toBe(50)
    expect(store.ageBand).toBe('6-8')
    expect(store.ageBandInfo.id).toBe('6-8')
  })

  it('setAffinity clamps to 0-100 and rounds', () => {
    const store = usePreferencesStore()
    store.setAffinity('playground', 187)
    expect(store.affinities.playground).toBe(100)
    store.setAffinity('playground', -20)
    expect(store.affinities.playground).toBe(0)
    store.setAffinity('playground', 42.6)
    expect(store.affinities.playground).toBe(43)
  })

  it('setAffinity ignores an unknown category', () => {
    const store = usePreferencesStore()
    store.setAffinity('not_a_category', 90)
    expect(store.affinities.not_a_category).toBeUndefined()
  })

  it('setAgeBand only accepts a known band id', () => {
    const store = usePreferencesStore()
    store.setAgeBand('9-12')
    expect(store.ageBand).toBe('9-12')
    expect(store.ageBandInfo).toBe(AGE_BANDS[2])

    store.setAgeBand('not-a-band')
    expect(store.ageBand).toBe('9-12') // unchanged
  })
})
