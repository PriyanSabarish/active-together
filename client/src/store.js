import { defineStore } from 'pinia'
import { postRecommendations, getContext } from './api'

// ---------------------------------------------------------------------------
// Places, weather and ranking all come from the backend now:
//   POST /recommendations  -> ranked combos (up to three)
//   GET  /data/context     -> current conditions for the time screen
//
// The only client-side table left is the suburb -> coordinate lookup below.
// The backend takes a latitude/longitude, not a suburb name, and there is no
// geocoding endpoint yet, so the client resolves the pilot suburbs itself.
// ---------------------------------------------------------------------------

// Approximate suburb centroids inside the three pilot LGAs
// (City of Melbourne, City of Monash, City of Melton).
export const SUBURB_COORDS = {
  // City of Melbourne
  'Carlton': { latitude: -37.8001, longitude: 144.9674 },
  'Carlton North': { latitude: -37.7845, longitude: 144.9722 },
  'Docklands': { latitude: -37.8149, longitude: 144.9462 },
  'East Melbourne': { latitude: -37.8157, longitude: 144.9871 },
  'Flemington': { latitude: -37.7878, longitude: 144.9302 },
  'Kensington': { latitude: -37.7941, longitude: 144.9303 },
  'Melbourne': { latitude: -37.8136, longitude: 144.9631 },
  'North Melbourne': { latitude: -37.7989, longitude: 144.9421 },
  'Parkville': { latitude: -37.7853, longitude: 144.9503 },
  'Southbank': { latitude: -37.8243, longitude: 144.9644 },
  'South Yarra': { latitude: -37.8386, longitude: 144.9924 },
  'West Melbourne': { latitude: -37.8078, longitude: 144.9403 },
  // City of Monash
  'Ashwood': { latitude: -37.8664, longitude: 145.1042 },
  'Chadstone': { latitude: -37.8873, longitude: 145.0952 },
  'Clarinda': { latitude: -37.9329, longitude: 145.1053 },
  'Clayton': { latitude: -37.9249, longitude: 145.1194 },
  'Clayton South': { latitude: -37.9411, longitude: 145.1233 },
  'Glen Waverley': { latitude: -37.8781, longitude: 145.1642 },
  'Hughesdale': { latitude: -37.8974, longitude: 145.0763 },
  'Huntingdale': { latitude: -37.9108, longitude: 145.1063 },
  'Mount Waverley': { latitude: -37.8767, longitude: 145.1293 },
  'Mulgrave': { latitude: -37.9262, longitude: 145.1781 },
  'Notting Hill': { latitude: -37.9067, longitude: 145.1424 },
  'Oakleigh': { latitude: -37.9004, longitude: 145.0888 },
  'Oakleigh East': { latitude: -37.8993, longitude: 145.1150 },
  'Oakleigh South': { latitude: -37.9223, longitude: 145.0912 },
  'Wheelers Hill': { latitude: -37.9021, longitude: 145.1866 },
  // City of Melton
  'Brookfield': { latitude: -37.7002, longitude: 144.5580 },
  'Burnside': { latitude: -37.7503, longitude: 144.7553 },
  'Caroline Springs': { latitude: -37.7418, longitude: 144.7372 },
  'Diggers Rest': { latitude: -37.6272, longitude: 144.7203 },
  'Eynesbury': { latitude: -37.7932, longitude: 144.6126 },
  'Fraser Rise': { latitude: -37.6901, longitude: 144.7292 },
  'Hillside': { latitude: -37.6893, longitude: 144.7502 },
  'Kurunjang': { latitude: -37.6690, longitude: 144.5902 },
  'Melton': { latitude: -37.6833, longitude: 144.5833 },
  'Melton South': { latitude: -37.7001, longitude: 144.5731 },
  'Melton West': { latitude: -37.6821, longitude: 144.5562 },
  'Rockbank': { latitude: -37.7302, longitude: 144.6563 },
  'Taylors Hill': { latitude: -37.7152, longitude: 144.7501 }
}

export const SUBURBS = Object.keys(SUBURB_COORDS).sort()

// The backend's DURATION_BUCKETS. Ties (30, 50) resolve to the lower bucket,
// matching app/recommendation/duration.py. Results carry the bucket the
// backend actually chose; this is only for the preview on the time screen.
export const DURATION_BUCKETS = [20, 40, 60]

export function matchBucket(durationMin) {
  return DURATION_BUCKETS.reduce((best, b) => {
    const d = Math.abs(durationMin - b)
    const bd = Math.abs(durationMin - best)
    return d < bd || (d === bd && b < best) ? b : best
  })
}

// The seven Vicmap categories the backend can return, with the icon shape
// used on the cards (canopy = park-like, ring = ground-like, zigzag = trail).
export const CATEGORY_META = {
  playground: { label: 'Playground', shape: 'park' },
  park_and_garden: { label: 'Park and garden', shape: 'park' },
  picnic_day_use: { label: 'Picnic and day-use area', shape: 'park' },
  sports_ground: { label: 'Sporting ground', shape: 'ground' },
  court: { label: 'Court', shape: 'ground' },
  skate_bmx: { label: 'Skate and BMX', shape: 'ground' },
  trail_access: { label: 'Trail', shape: 'trail' }
}

export function categoryLabel(category) {
  return CATEGORY_META[category]?.label ?? category.replace(/_/g, ' ')
}

function badgeFor(summary, tier) {
  if (summary && summary.available === false) return { type: 'muted', label: 'weather unavailable' }
  if (tier !== 'deprioritised') return { type: 'good', label: 'good fit' }
  const text = (summary?.warnings ?? []).join(' ').toLowerCase()
  if (text.includes('rain')) return { type: 'warn', label: 'rain risk' }
  if (text.includes('wind')) return { type: 'warn', label: 'windy' }
  if (text.includes('particle')) return { type: 'warn', label: 'air quality' }
  return { type: 'warn', label: 'conditions' }
}

function formatDistance(distanceM) {
  const km = distanceM / 1000
  return km >= 1 ? `${km.toFixed(1)} km` : `${Math.round(distanceM / 10) * 10} m`
}

function conditionsFor(summary) {
  if (!summary || !summary.available) {
    return [{ icon: 'unknown', text: 'Weather data is unavailable for this time.' }]
  }
  const rows = []
  const sky = []
  if (summary.temp_c != null) sky.push(`${Math.round(summary.temp_c)}°C`)
  if (summary.precip_prob != null) sky.push(`${Math.round(summary.precip_prob * 100)}% chance of rain`)
  if (sky.length) rows.push({ icon: 'sun', text: sky.join(' · ') })

  if (summary.uv_index != null) {
    const reminder = (summary.reminders ?? []).find((r) => /uv/i.test(r))
    rows.push({ icon: 'uv', text: reminder ? `UV ${summary.uv_index}, sun protection suggested` : `UV ${summary.uv_index}, low sun risk` })
  }

  if (summary.wind_gust_kmh != null) {
    const windy = (summary.warnings ?? []).some((w) => /wind/i.test(w))
    rows.push({ icon: windy ? 'wind' : 'check', text: `Wind gusts up to ${Math.round(summary.wind_gust_kmh)} km/h` })
  }

  if (summary.pm25 != null || summary.pm10 != null) {
    const parts = []
    if (summary.pm25 != null) parts.push(`PM2.5 ${Math.round(summary.pm25)}`)
    if (summary.pm10 != null) parts.push(`PM10 ${Math.round(summary.pm10)}`)
    const elevated = (summary.warnings ?? []).some((w) => /particle/i.test(w))
    rows.push({ icon: elevated ? 'wind' : 'check', text: `${elevated ? 'Elevated' : 'Good'} air quality · ${parts.join(', ')}` })
  }

  if (rows.length === 0) rows.push({ icon: 'unknown', text: 'Weather data is unavailable for this time.' })
  return rows
}

// The data pipeline labels places that have no official name as
// "Unnamed {Subtype} - {Council} - {Record ID}". For display (team decision)
// drop the word "Unnamed", move the record id into its own small tag, and
// keep the `unnamed` flag for styling.
const GENERATED_LABEL = /^\s*unnamed\s+(.*?)(?:\s*-\s*(\d+))?\s*$/i

export function displayName(rawName, label) {
  const raw = (rawName ?? '').trim()
  if (!raw) return { name: label, unnamed: true, recordId: null }
  const m = raw.match(GENERATED_LABEL)
  if (m) return { name: m[1].trim(), unnamed: true, recordId: m[2] ?? null }
  return { name: raw, unnamed: false, recordId: null }
}

// Convert one backend Combo into the flat shape the cards render.
export function mapCombo(combo, ctx) {
  const place = combo.place
  const summary = combo.environmental_summary ?? { available: false }
  const label = categoryLabel(place.activity_category)
  const { name, unnamed, recordId } = displayName(place.display_name, label)
  const distanceM = Number(place.distance_m ?? 0)
  const warnings = summary.warnings ?? []
  const reminders = summary.reminders ?? []

  const reasons = [
    `About ${formatDistance(distanceM)} away, within your ${ctx.radiusKm} km radius`,
    `Fits your ${combo.entered_duration_min}-min window using the ${combo.duration_bucket}-min plan`,
    ...warnings,
    ...reminders
  ]
  if (!summary.available) reasons.push('Weather data is unavailable for this time.')
  else if (warnings.length === 0 && reminders.length === 0) reasons.push('No weather or air-quality warnings right now')

  return {
    id: place.place_id,
    name,
    unnamed,
    recordId,
    category: place.activity_category,
    categoryLabel: label,
    lga: place.lga_name,
    latitude: place.latitude,
    longitude: place.longitude,
    distanceM,
    distanceKm: Math.round(distanceM / 100) / 10,
    tier: combo.tier,
    badge: badgeFor(summary, combo.tier),
    reason: combo.explanation,
    reasons,
    conditions: conditionsFor(summary),
    warnings,
    reminders,
    activityType: combo.activity_type,
    comboTitle: combo.combo_template,
    durationBucket: combo.duration_bucket,
    enteredDurationMin: combo.entered_duration_min,
    expect: `${combo.combo_template}: ${combo.activity_type}. Category-level suggestion based on open data. Not verified on site.`
  }
}

export const useSearchStore = defineStore('search', {
  state: () => ({
    // screen 1
    suburb: '',
    useMyLocation: false,
    myLocation: null, // { latitude, longitude } from the browser
    radiusKm: 5,
    recent: ['Carlton', 'Clayton'],
    // screen 2
    durationMin: 45,
    context: null, // GET /data/context payload for the chosen point
    contextLoading: false,
    // results
    loading: false,
    status: 'idle', // 'idle' | 'ok' | 'zero_results' | 'out_of_bounds' | 'error'
    message: '',
    error: '',
    results: [],
    _requestSeq: 0
  }),
  getters: {
    locationLabel(state) {
      if (state.useMyLocation) return 'your location'
      return state.suburb || 'your point'
    },
    coords(state) {
      if (state.useMyLocation) return state.myLocation
      return SUBURB_COORDS[state.suburb] ?? null
    },
    hasLocation() {
      return this.coords != null
    },
    weather(state) {
      return state.context
    },
    planMin(state) {
      return matchBucket(state.durationMin)
    },
    place(state) {
      return (id) => state.results.find((p) => p.id === id)
    }
  },
  actions: {
    rememberSuburb(name) {
      if (!name) return
      this.recent = [name, ...this.recent.filter((r) => r !== name)].slice(0, 3)
    },
    setMyLocation(coords) {
      this.myLocation = coords
      this.useMyLocation = true
      this.suburb = ''
    },
    // Current conditions for the chosen point, shown on the time screen.
    async loadContext() {
      const coords = this.coords
      if (!coords) {
        this.context = null
        return
      }
      this.contextLoading = true
      try {
        this.context = await getContext(coords)
      } catch {
        this.context = { available: false }
      } finally {
        this.contextLoading = false
      }
    },
    // POST /recommendations for the current location, radius and duration.
    async fetchRecommendations() {
      const coords = this.coords
      if (!coords) {
        this.status = 'idle'
        this.results = []
        return
      }
      const seq = ++this._requestSeq
      this.loading = true
      this.results = []
      this.status = 'idle'
      this.message = ''
      this.error = ''
      try {
        const data = await postRecommendations({
          latitude: coords.latitude,
          longitude: coords.longitude,
          radiusKm: this.radiusKm,
          durationMin: this.durationMin
        })
        if (seq !== this._requestSeq) return // a newer search superseded this one
        const ctx = { radiusKm: this.radiusKm }
        this.results = (data.combos ?? []).map((c) => mapCombo(c, ctx))
        this.status = data.status ?? (this.results.length ? 'ok' : 'zero_results')
        this.message = data.message ?? ''
      } catch (e) {
        if (seq !== this._requestSeq) return
        this.status = 'error'
        this.error = e?.message ?? 'Something went wrong.'
      } finally {
        if (seq === this._requestSeq) this.loading = false
      }
    }
  }
})
