<template>
  <AppHeader />
  <!-- Setup step 1: pick a starting point (device location or a pilot suburb) and a radius. -->

  <div class="scroll-area">
    <h1>Where are you starting?</h1>
    <p class="subtitle">Melbourne, Monash and Melton are covered so far.</p>

    <div class="start-card">
      <button class="loc-row use-location" :class="{ active: store.useMyLocation }" @click="pickMyLocation">
        <span class="loc-icon">
          <span v-if="locating" class="spinner" />
          <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">
            <circle cx="8" cy="8" r="5.5" /><circle cx="8" cy="8" r="1.6" fill="currentColor" stroke="none" />
            <path d="M8 1v2M8 13v2M1 8h2M13 8h2" stroke-linecap="round" />
          </svg>
        </span>
        <span class="loc-text">
          <span class="loc-title">{{ locating ? 'Locating…' : store.useMyLocation ? 'Using your location' : 'Use my location' }}</span>
          <span class="loc-sub" :class="{ err: locationError }">{{ locationError || 'Nearest suburb, nothing stored' }}</span>
        </span>
        <span class="loc-chev">›</span>
      </button>

      <!-- Vicmap address search, restricted by the backend to the pilot LGAs. -->
      <div class="search-row">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5 14 14" />
        </svg>
        <input
          v-model="query"
          type="text"
          placeholder="Enter a street address or suburb"
          @focus="open = true"
          @input="onInput"
        />
        <button v-if="query" class="clear-btn" aria-label="Clear" @click="clearQuery">×</button>
      </div>

      <div v-if="open && (searching || suggestions.length || searchMessage)" class="suggest-list">
        <p v-if="searching" class="suggest-status">Searching addresses…</p>
        <button v-for="s in suggestions" :key="s.id" class="suggest-item" @click="pickAddress(s)">
          {{ s.label }}
        </button>
        <p v-if="!searching && searchMessage" class="suggest-status">{{ searchMessage }}</p>
      </div>
    </div>
    <p class="address-attribution">
      Address data © State of Victoria, <a href="https://www.land.vic.gov.au/maps-and-spatial/spatial-data/vicmap-catalogue/vicmap-address" target="_blank" rel="noopener">CC BY 4.0</a>
    </p>

    <!-- Quick picks: recent suburbs first, topped up from the pilot list. -->
    <div class="chips">
      <button
        v-for="r in quickPicks"
        :key="r"
        class="pill"
        :class="{ on: store.suburb === r && !store.useMyLocation }"
        @click="pickSuburb(r)"
      >
        {{ r }}
      </button>
    </div>

    <p class="section-label" style="margin-top: 22px">Maximum distance</p>
    <div class="seg-row">
      <button
        v-for="km in [3, 5, 10]"
        :key="km"
        class="seg-btn radius-btn"
        :class="{ on: store.radiusKm === km }"
        @click="store.radiusKm = km"
      >
        {{ km }} km
      </button>
    </div>

    <!-- Radius preview around the chosen point. -->
    <PlaceMap class="map-preview" :center="store.coords" :radius-km="store.radiusKm" height="150px" />
    <p class="map-caption">{{ store.radiusKm }} km radius around {{ pointLabel }}</p>
  </div>

  <button class="btn btn-primary cta" :disabled="!ready" @click="next">
    {{ ready ? `Show places near ${ctaLabel}` : 'Pick a starting point first' }}
    <span class="btn-arrow">→</span>
  </button>
</template>

<script setup>
// Setup step 1 — choose browser geolocation, a quick-pick suburb, or a
// Vicmap address returned by the pilot-area autocomplete endpoint.

import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import PlaceMap from '../components/PlaceMap.vue'
import { searchAddresses } from '../api'
import { useSearchStore } from '../store'

const store = useSearchStore()
const router = useRouter()

const query = ref(store.selectedAddress?.label || store.suburb)
const open = ref(false)
const locating = ref(false)
const locationError = ref('')
const suggestions = ref([])
const searching = ref(false)
const searchMessage = ref('')
let searchTimer = null
let searchController = null
let searchSeq = 0

const ready = computed(() => store.hasLocation)

// Recent suburbs first, topped up with pilot-area suburbs so the chip row is
// never empty on a fresh install.
const FALLBACK = ['Clayton', 'Oakleigh', 'Carlton North', 'Glen Waverley', 'Melton South']
const quickPicks = computed(() => {
  const seen = new Set()
  return [...store.recent, ...FALLBACK].filter((s) => !seen.has(s) && seen.add(s)).slice(0, 5)
})

const pointLabel = computed(() => store.locationLabel)
const ctaLabel = computed(() => (store.useMyLocation ? 'you' : store.locationLabel))

function onInput() {
  store.useMyLocation = false
  store.suburb = ''
  store.selectedAddress = null
  suggestions.value = []
  searchMessage.value = ''
  open.value = true
  clearTimeout(searchTimer)
  searchController?.abort()
  searchSeq += 1
  const text = query.value.trim()
  if (text.length < 3) {
    searching.value = false
    return
  }
  searchTimer = setTimeout(() => runAddressSearch(text), 300)
}

async function runAddressSearch(text) {
  const seq = ++searchSeq
  searchController = new AbortController()
  searching.value = true
  try {
    const data = await searchAddresses(text, { signal: searchController.signal })
    if (seq !== searchSeq) return
    suggestions.value = data.suggestions ?? []
    searchMessage.value = suggestions.value.length ? '' : 'No matching address in the pilot areas.'
  } catch (error) {
    if (seq === searchSeq && error?.name !== 'AbortError') {
      searchMessage.value = 'Address search is temporarily unavailable.'
    }
  } finally {
    if (seq === searchSeq) searching.value = false
  }
}

function clearQuery() {
  query.value = ''
  store.suburb = ''
  store.selectedAddress = null
  suggestions.value = []
  searchMessage.value = ''
  searching.value = false
  searchSeq += 1
  clearTimeout(searchTimer)
  searchController?.abort()
}

function pickAddress(address) {
  query.value = address.label
  store.setAddress(address)
  locationError.value = ''
  open.value = false
}

function pickSuburb(suburb) {
  query.value = suburb
  store.suburb = suburb
  store.selectedAddress = null
  store.useMyLocation = false
  locationError.value = ''
  open.value = false
}

// Geolocation is requested only on tap, never on load; coordinates stay in
// memory (and in the persisted search inputs), no reverse geocoding.
function pickMyLocation() {
  if (locating.value) return
  locationError.value = ''
  if (!('geolocation' in navigator)) {
    locationError.value = 'Location is not available in this browser. Enter an address instead.'
    return
  }
  locating.value = true
  query.value = ''
  store.suburb = ''
  store.selectedAddress = null
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      locating.value = false
      store.setMyLocation({ latitude: pos.coords.latitude, longitude: pos.coords.longitude })
    },
    (err) => {
      locating.value = false
      store.useMyLocation = false
      locationError.value =
        err.code === err.PERMISSION_DENIED
          ? 'Location permission was denied. Enter an address instead.'
          : 'We could not get your location. Enter an address instead.'
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
  )
}

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  searchController?.abort()
})

function next() {
  if (store.suburb) store.rememberSuburb(store.suburb)
  router.push('/time')
}
</script>

<style scoped>
.start-card {
  position: relative;
  margin-top: 18px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  overflow: visible;
}

.loc-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: none;
  background: none;
  font-family: inherit;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
  border-bottom: 1px solid var(--line);
  border-radius: var(--radius-card) var(--radius-card) 0 0;
}

.loc-row.active { background: var(--green-light); }

.loc-icon {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--green);
  flex-shrink: 0;
}

.loc-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.loc-title { font-size: 15.5px; font-weight: 600; }
.loc-sub { font-size: 12.5px; color: var(--ink-3); }
.loc-sub.err { color: var(--amber); }
.loc-chev { font-size: 20px; color: var(--ink-4); line-height: 1; }

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--green);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: 50px;
  color: var(--ink-4);
}

.search-row input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  font-family: inherit;
  color: var(--ink);
}

.search-row input::placeholder { color: var(--ink-4); }

.clear-btn {
  border: none;
  background: var(--tint);
  color: var(--ink-3);
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}

.suggest-list {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--card);
  border-radius: var(--radius-field);
  box-shadow: var(--shadow-raised);
  z-index: 10;
  overflow: hidden;
}

.suggest-item {
  display: block;
  width: 100%;
  border: none;
  background: none;
  padding: 12px 16px;
  font-size: 14px;
  font-family: inherit;
  color: var(--ink);
  cursor: pointer;
  text-align: left;
}

.suggest-item:hover { background: var(--tint); }

.suggest-status {
  padding: 12px 16px;
  margin: 0;
  font-size: 12px;
  color: var(--ink-4);
}

.address-attribution {
  margin: 6px 2px 0;
  font-size: 9.5px;
  color: var(--ink-5);
}

.address-attribution a { color: inherit; }

.chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }

.map-preview { margin-top: 16px; }

.map-caption {
  text-align: center;
  font-size: 12px;
  color: var(--ink-4);
  margin-top: 8px;
}

.cta { width: 100%; margin-top: 14px; }
</style>
