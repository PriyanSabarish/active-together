// Iteration 2, F10 — unit tests for client/src/preferencesStore.js.

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePreferencesStore, AGE_BANDS, levelOf } from '../../client/src/preferencesStore'
import { sanitisePrefs } from '../../client/src/persist'
import { CATEGORY_META } from '../../client/src/store'

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('F10 — preferences store', () => {
  it('defaults every category to a neutral affinity and age band 8-10', () => {
    const store = usePreferencesStore()
    expect(Object.keys(store.affinities).sort()).toEqual(Object.keys(CATEGORY_META).sort())
    for (const v of Object.values(store.affinities)) expect(v).toBe(50)
    expect(store.ageBand).toBe('8-10')
    expect(store.ageBandInfo.id).toBe('8-10')
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
    store.setAgeBand('11-12')
    expect(store.ageBand).toBe('11-12')
    expect(store.ageBandInfo).toBe(AGE_BANDS[2])

    store.setAgeBand('not-a-band')
    expect(store.ageBand).toBe('11-12') // unchanged
  })
})

describe('Iteration 3 — three-way preferences reach the backend', () => {
  it('"Not for me" is excluded; Likes and No preference are not', () => {
    const store = usePreferencesStore()
    store.setLevel('sports_ground', 'nope')
    store.setLevel('playground', 'likes')
    store.setLevel('court', 'neutral')
    expect(store.excludedCategories).toEqual(['sports_ground'])
    expect(store.likedCategories).toEqual(['playground'])
  })

  it('levelOf reads stored affinities back as the three choices', () => {
    expect(levelOf(80)).toBe('likes')
    expect(levelOf(50)).toBe('neutral')
    expect(levelOf(20)).toBe('nope')
    expect(levelOf(0)).toBe('nope')
  })

  it('saved preferences are sanitised: unknown bands, categories and values are dropped', () => {
    const cats = Object.keys(CATEGORY_META)
    expect(sanitisePrefs({ ageBand: '5-7', affinities: { playground: 20, nope: 50, court: 300 } }, cats))
      .toEqual({ ageBand: '5-7', affinities: { playground: 20 } })
    expect(sanitisePrefs({ ageBand: 'adult' }, cats)).toEqual({})
    expect(sanitisePrefs('garbage', cats)).toEqual({})
  })
})
