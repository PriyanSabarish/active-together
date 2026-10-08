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

// Below this, a category counts as "excluded" for POST /missions' preferences
// list (app.recommendation.preferences / select_templates both treat it as a
// plain exclusion, not a weighted score) — the backend has no concept of the
// 0-100 slider itself. 20 was picked as "clearly dragged toward not
// interested", not just "slightly below neutral".
const EXCLUSION_THRESHOLD = 20

// What the kid likes, from the Start page's "Your kid" sheet: plain on/off
// interests (not place categories). Icons are 24x24 stroke paths.
export const KID_LIKES = [
  { name: 'Animals', icon: 'M8 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M16 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M5 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M19 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M12 12c-3 0-5 3-5 5.5S9 20 12 20s5-.5 5-2.5S15 12 12 12Z' },
  { name: 'Climbing', icon: 'M4 20 10 8l4 6 2-3 4 9Z' },
  { name: 'Building', icon: 'M4 20V10h6v10 M10 20V4h10v16 M4 20h16' },
  { name: 'Running', icon: 'M13 4.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z M9.5 21l2-6 2.5 2v4 M8 11l2.5-3.5 3 1.5 2 3' },
  { name: 'Drawing', icon: 'M4 20l4-1 11-11-3-3L5 16Z M14 6l3 3' },
  { name: 'Water', icon: 'M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z' }
]

export const usePreferencesStore = defineStore('preferences', {
  state: () => ({
    affinities: defaultAffinities(),
    ageBand: '8-10',
    kidLikes: [] // names from KID_LIKES
  }),
  getters: {
    ageBandInfo(state) {
      return AGE_BANDS.find((b) => b.id === state.ageBand) ?? AGE_BANDS[1]
    },
    excludedCategories(state) {
      return Object.entries(state.affinities)
        .filter(([, value]) => value < EXCLUSION_THRESHOLD)
        .map(([category]) => category)
    }
  },
  actions: {
    setAffinity(category, value) {
      if (!(category in this.affinities)) return
      this.affinities[category] = Math.min(100, Math.max(0, Math.round(value)))
    },
    setKidLikes(names) {
      this.kidLikes = KID_LIKES.map((l) => l.name).filter((n) => names.includes(n))
    },
    setAgeBand(bandId) {
      if (!AGE_BANDS.some((b) => b.id === bandId)) return
      this.ageBand = bandId
    }
  }
})
