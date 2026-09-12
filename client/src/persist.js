import { SUBURBS } from './store'

// Pinia plugin that keeps the parent's search inputs across a page reload.
//
// Only the inputs are stored (where, how far, how long). Results and the
// weather context are deliberately NOT persisted: once the inputs are back the
// views re-fetch them, so a reload never shows a stale recommendation.

export const STORAGE_KEY = 'at-search-v1'

const PERSISTED = ['suburb', 'selectedAddress', 'useMyLocation', 'myLocation', 'radiusKm', 'recent', 'durationMin']
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
  if (Number.isInteger(saved.durationMin) && saved.durationMin >= 20 && saved.durationMin <= 120) out.durationMin = saved.durationMin
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
