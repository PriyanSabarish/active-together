import { SUBURBS, SETTINGS, TRAVEL_MODES, TRAVEL_STOPS, STAY_STOPS } from './store'

// Pinia plugin that keeps the parent's search inputs across a page reload.
//
// Only the inputs are stored (where, how far, how long). Results and the
// weather context are deliberately NOT persisted: once the inputs are back the
// views re-fetch them, so a reload never shows a stale recommendation.

export const STORAGE_KEY = 'at-search-v1'

const PERSISTED = ['suburb', 'selectedAddress', 'useMyLocation', 'myLocation', 'radiusKm', 'recent', 'durationMin', 'setting', 'travelMode', 'travelMin', 'stayMin']
const RADII = [3, 5, 10]

function isCoords(v) {
  return v != null && Number.isFinite(v.latitude) && Number.isFinite(v.longitude)
}

// Drop anything that is not a value the UI could have produced itself, so a
// hand-edited or outdated entry cannot put the store into an impossible state.
export function sanitise(saved) {
  if (!saved || typeof saved !== 'object') return {}
  const out = {}
  if (SUBURBS.includes(saved.suburb)) out.suburb = saved.suburb
  if (isCoords(saved.selectedAddress) && typeof saved.selectedAddress.label === 'string') {
    out.selectedAddress = {
      id: String(saved.selectedAddress.id ?? ''),
      label: saved.selectedAddress.label.slice(0, 200),
      latitude: saved.selectedAddress.latitude,
      longitude: saved.selectedAddress.longitude,
      suburb: String(saved.selectedAddress.suburb ?? '').slice(0, 100),
      postcode: String(saved.selectedAddress.postcode ?? '').slice(0, 4)
    }
  }
  if (isCoords(saved.myLocation)) out.myLocation = { latitude: saved.myLocation.latitude, longitude: saved.myLocation.longitude }
  if (saved.useMyLocation === true && out.myLocation) out.useMyLocation = true
  if (RADII.includes(saved.radiusKm)) out.radiusKm = saved.radiusKm
  if (Number.isInteger(saved.durationMin) && saved.durationMin >= 20 && saved.durationMin <= 60) out.durationMin = saved.durationMin
  if (SETTINGS.includes(saved.setting)) out.setting = saved.setting
  if (TRAVEL_MODES.includes(saved.travelMode)) out.travelMode = saved.travelMode
  if (TRAVEL_STOPS.includes(saved.travelMin)) out.travelMin = saved.travelMin
  if (STAY_STOPS.includes(saved.stayMin)) out.stayMin = saved.stayMin
  if (Array.isArray(saved.recent)) out.recent = saved.recent.filter((r) => SUBURBS.includes(r)).slice(0, 3)
  return out
}

function pick(state) {
  return Object.fromEntries(PERSISTED.map((k) => [k, state[k]]))
}

export function persistSearchState({ store }) {
  if (store.$id !== 'search') return

  let storage
  try {
    storage = window.localStorage
  } catch {
    return // storage blocked (private mode, sandbox): behave as before
  }

  try {
    const raw = storage.getItem(STORAGE_KEY)
    if (raw) store.$patch(sanitise(JSON.parse(raw)))
  } catch {
    /* corrupt entry: ignore and start fresh */
  }

  store.$subscribe(
    (_mutation, state) => {
      try {
        storage.setItem(STORAGE_KEY, JSON.stringify(pick(state)))
      } catch {
        /* quota or storage unavailable: nothing to do */
      }
    },
    // sync: write immediately so a reload right after a change still sees it
    { detached: true, flush: 'sync' }
  )
}

// ---------------------------------------------------------------------------
// Preferences (age band and the per-category Likes / No preference / Not for
// me) are kept the same way, so a reload never quietly drops an exclusion.
// ---------------------------------------------------------------------------

export const PREFS_KEY = 'at-prefs-v1'
const AGE_BAND_IDS = ['5-7', '8-10', '11-12']

export function sanitisePrefs(saved, categories) {
  if (!saved || typeof saved !== 'object') return {}
  const out = {}
  if (AGE_BAND_IDS.includes(saved.ageBand)) out.ageBand = saved.ageBand
  if (saved.affinities && typeof saved.affinities === 'object') {
    const aff = {}
    for (const c of categories) {
      const v = saved.affinities[c]
      if (Number.isFinite(v) && v >= 0 && v <= 100) aff[c] = Math.round(v)
    }
    if (Object.keys(aff).length) out.affinities = aff
  }
  return out
}

export function hasSavedPreferences() {
  try {
    return window.localStorage.getItem(PREFS_KEY) != null
  } catch {
    return false
  }
}

export function persistPreferences({ store }) {
  if (store.$id !== 'preferences') return

  let storage
  try {
    storage = window.localStorage
  } catch {
    return
  }

  try {
    const raw = storage.getItem(PREFS_KEY)
    if (raw) {
      const clean = sanitisePrefs(JSON.parse(raw), Object.keys(store.affinities))
      if (clean.affinities) clean.affinities = { ...store.affinities, ...clean.affinities }
      store.$patch(clean)
    }
  } catch {
    /* corrupt entry: ignore and start fresh */
  }

  store.$subscribe(
    (_mutation, state) => {
      try {
        storage.setItem(PREFS_KEY, JSON.stringify({ ageBand: state.ageBand, affinities: state.affinities }))
      } catch {
        /* quota or storage unavailable */
      }
    },
    { detached: true, flush: 'sync' }
  )
}
