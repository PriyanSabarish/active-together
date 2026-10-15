import { defineStore } from 'pinia'
import { CATEGORY_META } from './store'

// ---------------------------------------------------------------------------
// F10 — preferences store. Each place category has a 0-100 affinity, set
// through a three-way choice (Likes / No preference / Not for me) on the
// Start page's "Your kid" sheet and on You → Likes. Age band is stored as a
// band only, never a date of birth. Saved on the device (persist.js).
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

// At or below this, a category counts as "excluded": it is sent as
// excluded_categories to POST /recommendations and as preferences to POST
// /missions, and the backend drops those places and templates. The backend
// only knows exclusion, so "Likes" is shown back to the parent but does not
// change the ranking yet.
const EXCLUSION_THRESHOLD = 20

// The three choices and the affinity each one stores.
export const PREF_LEVELS = [
  { id: 'likes', label: 'Likes', value: 80 },
  { id: 'neutral', label: 'No preference', value: 50 },
  { id: 'nope', label: 'Not for me', value: 20 }
]

// 0-100 affinity -> which of the three choices it reads as.
export function levelOf(value) {
  if (value >= 67) return 'likes'
  if (value > EXCLUSION_THRESHOLD) return 'neutral'
  return 'nope'
}

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    affinities: defaultAffinities(),
    ageBand: '8-10'
  }),
  getters: {
    ageBandInfo(state) {
      return AGE_BANDS.find((b) => b.id === state.ageBand) ?? AGE_BANDS[1]
    },
    excludedCategories(state) {
      return Object.entries(state.affinities)
        .filter(([, value]) => value <= EXCLUSION_THRESHOLD)
        .map(([category]) => category)
    },
    likedCategories(state) {
      return Object.entries(state.affinities)
        .filter(([, value]) => levelOf(value) === 'likes')
        .map(([category]) => category)
    }
  },
  actions: {
    setAffinity(category, value) {
      if (!(category in this.affinities)) return
      this.affinities[category] = Math.min(100, Math.max(0, Math.round(value)))
    },
    setLevel(category, levelId) {
      const level = PREF_LEVELS.find((l) => l.id === levelId)
      if (level) this.setAffinity(category, level.value)
    },
    setAgeBand(bandId) {
      if (!AGE_BANDS.some((b) => b.id === bandId)) return
      this.ageBand = bandId
    }
  }
})
