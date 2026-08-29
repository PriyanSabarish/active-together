import { defineStore } from 'pinia'

// ---------------------------------------------------------------------------
// All data below is FABRICATED for the demo. When the FastAPI backend is
// ready, replace fetchRecommendations() with a real call to
// POST /api/recommendations and delete the mock tables.
// ---------------------------------------------------------------------------

export const SUBURBS = [
  'Carlton', 'Fitzroy', 'Brunswick', 'Richmond', 'South Yarra',
  'Parkville', 'Clayton', 'Glen Waverley', 'Mount Waverley', 'Melton'
]

// Mock hourly forecast for "today" (Open-Meteo stand-in).
export const FORECAST = [
  { h: 9,  label: '9:00 AM',  temp: 16, rain: 10, wind: 12, uv: 2, desc: 'partly cloudy' },
  { h: 10, label: '10:00 AM', temp: 18, rain: 10, wind: 14, uv: 3, desc: 'partly cloudy' },
  { h: 11, label: '11:00 AM', temp: 19, rain: 5,  wind: 16, uv: 4, desc: 'mostly sunny' },
  { h: 12, label: '12:00 PM', temp: 21, rain: 5,  wind: 18, uv: 5, desc: 'sunny' },
  { h: 13, label: '1:00 PM',  temp: 22, rain: 5,  wind: 20, uv: 5, desc: 'sunny' },
  { h: 14, label: '2:00 PM',  temp: 22, rain: 10, wind: 24, uv: 4, desc: 'mostly sunny' },
  { h: 15, label: '3:00 PM',  temp: 22, rain: 10, wind: 26, uv: 4, desc: 'mostly sunny' },
  { h: 16, label: '4:00 PM',  temp: 22, rain: 10, wind: 26, uv: 4, desc: 'mostly sunny' },
  { h: 17, label: '5:00 PM',  temp: 21, rain: 20, wind: 30, uv: 2, desc: 'clouding over' },
  { h: 18, label: '6:00 PM',  temp: 19, rain: 35, wind: 28, uv: 1, desc: 'cloudy' }
]

const CATEGORY_META = {
  park: {
    label: 'Park and playground',
    exposure: 'sheltered',
    expect: 'Category-level suggestion: playgrounds and open lawn typically found here. Not verified.'
  },
  ground: {
    label: 'Sporting ground',
    exposure: 'open',
    expect: 'Category-level suggestion: open oval and marked courts typically found here. Not verified.'
  },
  trail: {
    label: 'Trail',
    exposure: 'exposed',
    expect: 'Category-level suggestion: shared walking and cycling path. Not verified.'
  }
}

// Candidate places per starting point. Distances are made up but plausible.
// Melton is deliberately sparse: 0 results at 3 km, 1 at 5 km, 3 at 10 km —
// it demos the zero/single-result variants and the adaptive-radius story.
const PLACES = {
  Carlton: [
    { id: 'argyle-square', name: 'Argyle Square', category: 'park', km: 0.4 },
    { id: 'fawkner-park', name: 'Fawkner Park', category: 'park', km: 0.6 },
    { id: 'uni-oval', name: 'University Square Oval', category: 'ground', km: 1.1 },
    { id: 'princes-park', name: 'Princes Park Reserve', category: 'ground', km: 1.4 },
    { id: 'royal-park-trail', name: 'Royal Park Trail', category: 'trail', km: 2.1 },
    { id: 'capital-city-trail', name: 'Capital City Trail', category: 'trail', km: 2.8 }
  ],
  Fitzroy: [
    { id: 'edinburgh-gardens', name: 'Edinburgh Gardens', category: 'park', km: 0.5 },
    { id: 'alfred-crescent', name: 'Alfred Crescent Oval', category: 'ground', km: 0.7 },
    { id: 'darling-gardens', name: 'Darling Gardens', category: 'park', km: 1.6 },
    { id: 'merri-creek-trail', name: 'Merri Creek Trail', category: 'trail', km: 1.9 }
  ],
  Brunswick: [
    { id: 'gilpin-park', name: 'Gilpin Park', category: 'park', km: 0.8 },
    { id: 'brunswick-velodrome', name: 'Brunswick Velodrome', category: 'ground', km: 1.0 },
    { id: 'merri-creek-trail-b', name: 'Merri Creek Trail', category: 'trail', km: 1.2 },
    { id: 'princes-park-b', name: 'Princes Park Reserve', category: 'ground', km: 2.4 }
  ],
  Richmond: [
    { id: 'citizens-park', name: 'Citizens Park', category: 'ground', km: 0.6 },
    { id: 'burnley-park', name: 'Burnley Park', category: 'park', km: 1.3 },
    { id: 'yarra-trail-r', name: 'Main Yarra Trail', category: 'trail', km: 1.7 }
  ],
  'South Yarra': [
    { id: 'fawkner-park-sy', name: 'Fawkner Park', category: 'park', km: 0.9 },
    { id: 'yarra-trail-sy', name: 'Yarra River Trail', category: 'trail', km: 1.4 },
    { id: 'como-park', name: 'Como Park', category: 'ground', km: 1.8 }
  ],
  Parkville: [
    { id: 'royal-park', name: 'Royal Park', category: 'park', km: 0.5 },
    { id: 'ryder-oval', name: 'Ryder Oval', category: 'ground', km: 0.9 },
    { id: 'capital-city-trail-p', name: 'Capital City Trail', category: 'trail', km: 1.1 }
  ],
  Clayton: [
    { id: 'clayton-reserve', name: 'Clayton Reserve', category: 'ground', km: 0.9 },
    { id: 'namatjira-park', name: 'Namatjira Park', category: 'park', km: 1.2 },
    { id: 'djerring-trail', name: 'Djerring Trail', category: 'trail', km: 1.5 }
  ],
  'Glen Waverley': [
    { id: 'central-reserve', name: 'Central Reserve', category: 'ground', km: 1.0 },
    { id: 'valley-reserve', name: 'Valley Reserve', category: 'park', km: 2.2 },
    { id: 'scotchmans-creek', name: "Scotchmans Creek Trail", category: 'trail', km: 2.6 }
  ],
  'Mount Waverley': [
    { id: 'mt-waverley-reserve', name: 'Mount Waverley Reserve', category: 'ground', km: 0.8 },
    { id: 'damper-creek', name: 'Damper Creek Reserve', category: 'park', km: 1.6 },
    { id: 'scotchmans-creek-mw', name: "Scotchmans Creek Trail", category: 'trail', km: 2.0 }
  ],
  Melton: [
    { id: 'hannah-watts', name: 'Hannah Watts Park', category: 'park', km: 4.2 },
    { id: 'navan-park', name: 'Navan Park', category: 'ground', km: 5.8 },
    { id: 'toolern-creek', name: 'Toolern Creek Trail', category: 'trail', km: 7.5 }
  ]
}

function forecastFor(hour) {
  return FORECAST.find((f) => f.h === hour) ?? FORECAST[FORECAST.length - 1]
}

function windWord(wind) {
  if (wind >= 28) return 'strong wind'
  if (wind >= 20) return 'fresh wind'
  return 'light wind'
}

function rainWord(rain) {
  if (rain >= 50) return 'High rain chance'
  if (rain >= 25) return 'Medium rain chance'
  return 'Low rain chance'
}

// Rule-based badge: worst applicable condition wins, matching the doc's
// transparent-ranking approach.
function badgeFor(place, wx) {
  const exposure = CATEGORY_META[place.category].exposure
  if (wx.rain >= 50) return { type: 'warn', label: 'rain risk' }
  if (wx.wind >= 24 && exposure === 'exposed') return { type: 'warn', label: 'windy' }
  if (wx.uv >= 8) return { type: 'warn', label: 'high UV' }
  return { type: 'good', label: 'good fit' }
}

function buildResult(place, index, ctx) {
  const meta = CATEGORY_META[place.category]
  const badge = badgeFor(place, ctx.wx)
  const warn = badge.type === 'warn'

  let reason
  if (warn && badge.label === 'windy') reason = 'Further away; wind gusts today.'
  else if (warn && badge.label === 'rain risk') reason = 'Rain is likely around that time.'
  else if (index === 0) reason = 'Closest option, fits your time window.'
  else reason = 'Fits your duration with room to spare.'

  const reasons = [
    `${place.km} km away, within your ${ctx.radiusKm} km radius`,
    `Fits your ${ctx.durationMin}-min window with room to spare`,
    warn
      ? badge.label === 'windy'
        ? 'Wind gusts forecast around that time'
        : 'Rain is likely around that time'
      : 'No weather or air-quality warnings right now'
  ]

  const conditions = [
    { icon: 'sun', text: `${ctx.wx.temp}°C · ${rainWord(ctx.wx.rain).toLowerCase()} · ${windWord(ctx.wx.wind)}` },
    { icon: 'uv', text: `UV ${ctx.wx.uv}, ${ctx.wx.uv >= 3 ? 'sun protection recommended' : 'low sun risk'}` },
    warn && badge.label === 'windy'
      ? { icon: 'wind', text: `Wind gusts up to ${ctx.wx.wind + 9} km/h around that time` }
      : { icon: 'check', text: 'Good air quality · PM2.5 12, PM10 18' }
  ]

  return {
    id: place.id,
    name: place.name,
    category: place.category,
    categoryLabel: meta.label,
    distanceKm: place.km,
    badge,
    reason,
    reasons,
    conditions,
    expect: meta.expect
  }
}

export const useSearchStore = defineStore('search', {
  state: () => ({
    // screen 1
    suburb: '',
    useMyLocation: false,
    radiusKm: 5,
    recent: ['Carlton', 'Fitzroy'],
    // screen 2
    timeMode: 'now', // 'now' | 'pick'
    hour: 16,
    durationMin: 45,
    // results
    loading: false,
    results: []
  }),
  getters: {
    locationLabel(state) {
      if (state.useMyLocation) return 'your location'
      return state.suburb || 'Carlton'
    },
    effectiveSuburb(state) {
      if (state.useMyLocation) return 'Carlton' // demo: "my location" resolves near Carlton
      return SUBURBS.includes(state.suburb) ? state.suburb : 'Carlton'
    },
    effectiveHour(state) {
      if (state.timeMode === 'now') {
        const h = new Date().getHours()
        return Math.min(Math.max(h, 9), 18)
      }
      return state.hour
    },
    weather() {
      return forecastFor(this.effectiveHour)
    },
    // Ties at 30 or 50 min round to the lower plan.
    planMin(state) {
      if (state.durationMin < 30) return 20
      if (state.durationMin < 50) return 40
      if (state.durationMin < 70) return 60
      if (state.durationMin < 90) return 80
      if (state.durationMin < 110) return 100
      return 120
    }
  },
  actions: {
    rememberSuburb(name) {
      if (!name) return
      this.recent = [name, ...this.recent.filter((r) => r !== name)].slice(0, 3)
    },
    // Simulated POST /api/recommendations — swap for a real fetch later.
    async fetchRecommendations() {
      this.loading = true
      this.results = []
      await new Promise((r) => setTimeout(r, 700))

      const candidates = PLACES[this.effectiveSuburb] ?? []
      const ctx = { wx: this.weather, radiusKm: this.radiusKm, durationMin: this.durationMin }
      this.results = candidates
        .filter((p) => p.km <= this.radiusKm)
        .sort((a, b) => a.km - b.km)
        .slice(0, 3)
        .map((p, i) => buildResult(p, i, ctx))
      this.loading = false
    }
  }
})
