import { defineStore } from 'pinia'

// ---------------------------------------------------------------------------
// All data below is FABRICATED for the demo. When the FastAPI backend is
// ready, replace it with real API calls and delete the mock tables.
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

function forecastFor(hour) {
  return FORECAST.find((f) => f.h === hour) ?? FORECAST[FORECAST.length - 1]
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
    // Placeholder until the results screen lands — will simulate
    // POST /api/recommendations and later become a real fetch.
    async fetchRecommendations() {
      this.loading = true
      this.results = []
      this.loading = false
    }
  }
})
