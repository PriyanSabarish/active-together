import { defineStore } from 'pinia'
import { CATEGORY_META } from './store'

// ---------------------------------------------------------------------------
// F10 — preferences store. Each activity type gets a 0-100 affinity slider
// (degree of preference) instead of a three-state like/no-preference/
// not-interested toggle — a deliberate interaction-model change from earlier
// drafts. Age band is stored as a band only, never a date of birth.
// ---------------------------------------------------------------------------

export const AGE_BANDS = [
  { id: '5-7', label: '5–7 years', note: 'Missions assume no independent reading at all.' },
  { id: '8-10', label: '8–10 years', note: 'Missions assume some reading and basic independence.' },
  { id: '11-12', label: '11–12 years', note: 'Missions can assume independent reading and more autonomy.' }
]

function defaultAffinities() {
  // Neutral by default — nothing is pre-favoured until a parent sets it.
  return Object.fromEntries(Object.keys(CATEGORY_META).map((c) => [c, 50]))
}

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    affinities: defaultAffinities(),
    ageBand: '8-10'
  }),
  getters: {
    ageBandInfo(state) {
      return AGE_BANDS.find((b) => b.id === state.ageBand) ?? AGE_BANDS[1]
    }
  },
  actions: {
    setAffinity(category, value) {
      if (!(category in this.affinities)) return
      this.affinities[category] = Math.min(100, Math.max(0, Math.round(value)))
    },
    setAgeBand(bandId) {
      if (!AGE_BANDS.some((b) => b.id === bandId)) return
      this.ageBand = bandId
    }
  }
})
