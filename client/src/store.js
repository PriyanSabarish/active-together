import { defineStore } from 'pinia'

// ---------------------------------------------------------------------------
// All data below is FABRICATED for the demo. When the FastAPI backend is
// ready, replace it with real API calls and delete the mock tables.
// ---------------------------------------------------------------------------

export const SUBURBS = [
  'Carlton', 'Fitzroy', 'Brunswick', 'Richmond', 'South Yarra',
  'Parkville', 'Clayton', 'Glen Waverley', 'Mount Waverley', 'Melton'
]

export const useSearchStore = defineStore('search', {
  state: () => ({
    // screen 1
    suburb: '',
    useMyLocation: false,
    radiusKm: 5,
    recent: ['Carlton', 'Fitzroy']
  }),
  getters: {
    locationLabel(state) {
      if (state.useMyLocation) return 'your location'
      return state.suburb || 'Carlton'
    },
    effectiveSuburb(state) {
      if (state.useMyLocation) return 'Carlton' // demo: "my location" resolves near Carlton
      return SUBURBS.includes(state.suburb) ? state.suburb : 'Carlton'
    }
  },
  actions: {
    rememberSuburb(name) {
      if (!name) return
      this.recent = [name, ...this.recent.filter((r) => r !== name)].slice(0, 3)
    }
  }
})
