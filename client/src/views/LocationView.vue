<template>
  <AppHeader :step="1" />

  <div class="scroll-area">
  <h1>Where are you starting from</h1>
  <p class="subtitle">Covers Melbourne, Monash and Melton for now.</p>

  <button class="use-location" :class="{ active: store.useMyLocation }" @click="pickMyLocation">
    <svg v-if="!locating" width="14" height="20" viewBox="0 0 14 20">
      <path d="M1 7 C1 3.5 3.7 1 7 1 C10.3 1 13 3.5 13 7 C13 11 7 19 7 19 C7 19 1 11 1 7 Z" fill="currentColor" />
      <circle cx="7" cy="7" r="2.3" fill="#EAF3DE" />
    </svg>
    <span v-else class="spinner" />
    {{ locating ? 'Locating…' : store.useMyLocation ? 'Using your location' : 'Use my location' }}
  </button>
  <p v-if="locationError" class="location-error">{{ locationError }}</p>

  <div class="or-row"><span class="or-line" /><span class="or-text">or</span><span class="or-line" /></div>

  <div class="suburb-wrap">
    <div class="suburb-field">
      <svg width="12" height="16" viewBox="0 0 14 20">
        <path d="M1 7 C1 3.5 3.7 1 7 1 C10.3 1 13 3.5 13 7 C13 11 7 19 7 19 C7 19 1 11 1 7 Z" fill="#B4B2A9" />
        <circle cx="7" cy="7" r="2" fill="#FFFFFF" />
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
        <svg width="10" height="14" viewBox="0 0 14 20">
          <path d="M1 7 C1 3.5 3.7 1 7 1 C10.3 1 13 3.5 13 7 C13 11 7 19 7 19 C7 19 1 11 1 7 Z" fill="#B4B2A9" />
        </svg>
        {{ s.label }}
      </button>
      <p v-if="!searching && searchMessage" class="suggest-status">{{ searchMessage }}</p>
    </div>
  </div>
  <p class="address-attribution">
    Address data © State of Victoria, <a href="https://www.land.vic.gov.au/maps-and-spatial/spatial-data/vicmap-catalogue/vicmap-address" target="_blank" rel="noopener">CC BY 4.0</a>
  </p>

  <p class="recent-label">Recent</p>
  <div class="recent-chips">
    <button v-for="r in store.recent" :key="r" class="chip" :class="{ on: store.suburb === r && !store.useMyLocation }" @click="pickSuburb(r)">
      {{ r }}, VIC
    </button>
  </div>

  <PlaceMap class="map-preview" :center="store.coords" :radius-km="store.radiusKm" height="172px" />
  <p class="map-caption">{{ store.radiusKm }} km radius around {{ pointLabel }}</p>

  <p class="section-label" style="margin-top: 20px">Maximum distance</p>
  <div class="radius-row">
    <button
      v-for="km in [3, 5, 10]"
      :key="km"
      class="radius-btn"
      :class="{ on: store.radiusKm === km }"
      @click="store.radiusKm = km"
    >
      {{ km }} km
    </button>
  </div>
  </div>

  <hr class="divider" style="margin-bottom: 16px" />
  <button class="btn btn-primary" :disabled="!ready" @click="next">Next</button>
</template>

<script setup>
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

const pointLabel = computed(() => store.locationLabel)

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
  if (text.length < 3) return
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
    if (seq === searchSeq && error?.name !== 'AbortError') searchMessage.value = 'Address search is temporarily unavailable.'
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
  searchSeq += 1
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
    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
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
.use-location {
  margin-top: 20px;
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 10px;
  background: var(--green-light);
  color: var(--green-dark);
  font-size: 14.5px;
  font-weight: 500;
  font-family: inherit;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 17px;
  cursor: pointer;
}

.use-location.active { outline: 2px solid var(--green); }

.location-error {
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--amber);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--green-dark);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.or-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.or-line { flex: 1; height: 1px; background: var(--line-2); }
.or-text { font-size: 11px; color: var(--ink-5); }

.suburb-wrap { position: relative; }

.suburb-field {
  height: 48px;
  border: 1px solid var(--line-3);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 15px;
  background: #FFFFFF;
}

.suburb-field input {
  border: none;
  outline: none;
  flex: 1;
  font-size: 14px;
  font-family: inherit;
  color: var(--ink);
  background: transparent;
}

.suburb-field input::placeholder { color: var(--ink-4); }

.clear-btn {
  border: none;
  background: var(--paper);
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
  top: 52px;
  left: 0;
  right: 0;
  background: #FFFFFF;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  box-shadow: 0 8px 20px rgba(44, 44, 42, 0.08);
  z-index: 10;
  overflow: hidden;
}

.suggest-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: none;
  background: none;
  padding: 12px 15px;
  font-size: 13.5px;
  font-family: inherit;
  color: var(--ink);
  cursor: pointer;
  text-align: left;
}

.suggest-item:hover { background: var(--paper); }

.suggest-status {
  padding: 12px 15px;
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

.recent-label {
  font-size: 11.5px;
  color: var(--ink-4);
  margin: 18px 0 8px;
}

.recent-chips { display: flex; gap: 8px; flex-wrap: wrap; }

.chip {
  height: 30px;
  padding: 0 16px;
  border-radius: 15px;
  border: 1px solid transparent;
  background: var(--paper);
  color: var(--ink-2);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
}

.chip.on {
  border-color: var(--green);
  background: var(--green-light);
  color: var(--green-dark);
}

.map-preview { margin-top: 16px; }

.map-caption {
  text-align: center;
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 8px;
}

.radius-row { display: flex; gap: 8px; }

.radius-btn {
  flex: 1;
  height: 44px;
  border-radius: 10px;
  border: 1px solid var(--line-3);
  background: #FFFFFF;
  color: var(--ink-2);
  font-size: 13.5px;
  font-family: inherit;
  cursor: pointer;
}

.radius-btn.on {
  background: var(--green);
  border-color: var(--green);
  color: var(--green-light);
  font-weight: 500;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: default;
}
</style>
