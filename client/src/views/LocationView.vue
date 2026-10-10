<template>
  <AppHeader>
    <template #right>
      <button class="env-pill" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="ENV[store.setting].icon" /></svg>
        {{ ENV[store.setting].label }}
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#56625A" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path :d="menuOpen ? 'M6 15l6-6 6 6' : 'M6 9l6 6 6-6'" /></svg>
      </button>
    </template>
  </AppHeader>

  <!-- Outdoors / At home / Indoor place (story 9.1) -->
  <div v-if="menuOpen" class="env-menu" role="menu">
    <button v-for="(e, key) in ENV" :key="key" class="env-opt" :class="{ on: store.setting === key }" role="menuitemradio" :aria-checked="store.setting === key" @click="pickSetting(key)">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="e.icon" /></svg>
      <span class="env-opt-label">{{ e.label }}</span>
      <svg v-if="store.setting === key" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
    </button>
  </div>

  <div class="scroll-area start" @click="menuOpen = false">
    <!-- 1 · Where are you starting? -->
    <section v-if="showFrom" class="from">
      <svg v-if="isOutdoor" class="from-sun" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#E8913A" stroke-width="2" stroke-linecap="round"><path d="M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z M12 2.5v2 M12 19.5v2 M2.5 12h2 M19.5 12h2 M5.3 5.3l1.4 1.4 M17.3 17.3l1.4 1.4 M5.3 18.7l1.4-1.4 M17.3 6.7l1.4-1.4" /></svg>
      <h1 class="from-title"><span class="num light">1</span>Where are you starting?</h1>

      <div class="from-row">
        <div class="field" :class="{ ok: store.hasLocation, err: !!locationError }">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="rgba(242,241,236,.75)" stroke-width="2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5" /><path d="M15.5 15.5 21 21" /></svg>
          <input
            v-model="query"
            type="text"
            placeholder="Search address or suburb"
            @focus="open = true"
            @input="onInput"
          />
          <svg v-if="store.hasLocation" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B4D278" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
          <button v-else-if="query" class="clear-btn" aria-label="Clear" @click="clearQuery">×</button>
        </div>
        <button class="use-location" :class="{ active: store.useMyLocation }" @click="pickMyLocation">
          <span class="loc-circle">
            <span v-if="locating" class="spinner" />
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 3 3 10.5l7.5 2.5L13 21Z" /></svg>
          </span>
          <span class="loc-label">{{ store.useMyLocation ? 'Located' : 'Locate' }}</span>
        </button>
      </div>

      <p v-if="locationError" class="from-error">{{ locationError }}</p>

      <div v-if="open && (searching || suggestions.length || searchMessage)" class="suggest-list">
        <p v-if="searching" class="suggest-status">Searching addresses…</p>
        <button v-for="s in suggestions" :key="s.id" class="suggest-item" @click="pickAddress(s)">{{ s.label }}</button>
        <p v-if="!searching && searchMessage" class="suggest-status">{{ searchMessage }}</p>
      </div>

      <div class="chips">
        <button v-for="r in quickPicks" :key="r" class="chip" :class="{ on: store.suburb === r && !store.useMyLocation }" @click="pickSuburb(r)">{{ r }}</button>
      </div>
      <p class="attribution">
        Address data © State of Victoria, <a href="https://www.land.vic.gov.au/maps-and-spatial/spatial-data/vicmap-catalogue/vicmap-address" target="_blank" rel="noopener">CC BY 4.0</a>
      </p>
    </section>

    <div class="steps">
      <!-- How far? travel minutes each way, walking or driving -->
      <section v-if="showFar" class="step">
        <div class="step-head">
          <h2><span class="num">{{ nums.far }}</span>How far?</h2>
          <div class="modes">
            <button v-for="m in MODES" :key="m.id" class="mode" :class="{ on: store.travelMode === m.id }" @click="store.setTravel({ mode: m.id })">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="m.icon" /></svg>
              {{ m.label }}
            </button>
          </div>
        </div>
        <p class="big"><b>{{ store.travelMin }}</b>min {{ modeWord }}, each way</p>
        <SegBar :stops="TRAVEL_STOPS" :value="store.travelMin" label="Travel minutes each way" item-class="travel-btn" @pick="(v) => store.setTravel({ minutes: v })" />
      </section>

      <!-- When? hourly forecast strip (outdoors only) -->
      <section v-if="isOutdoor" class="step">
        <div class="step-head"><h2><span class="num">{{ nums.when }}</span>When?</h2></div>
        <div ref="stripEl" class="strip">
          <button v-for="c in cells" :key="c.key" class="cell" :class="{ on: c.key === selectedKey }" @click="store.whenAt = c.iso">
            <span class="cell-day">{{ c.day }}</span>
            <span class="cell-t">{{ c.t }}</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" :stroke="c.key === selectedKey ? '#FFFFFF' : c.ic" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="WX_ICON[c.icon]" /></svg>
            <span class="cell-temp">{{ c.temp }}</span>
          </button>
        </div>
        <p v-if="store.hasLocation" class="wx-note" :class="{ wet: selectedWx?.wet }">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="WX_ICON[selectedWx?.icon ?? 'cloud']" /></svg>
          {{ wxText }}
        </p>
      </section>

      <!-- How long there? / How long to play? -->
      <section v-if="showThere" class="step">
        <div class="step-head">
          <h2><span class="num">{{ nums.there }}</span>{{ isHome ? 'How long to play?' : 'How long there?' }}</h2>
          <span v-if="isOutdoor" class="outing-pill">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 7.5V12l3 2 M12 20.5a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17Z" /></svg>
            {{ fmt(store.travelMin * 2 + store.stayMin) }} outing
          </span>
        </div>
        <p class="big"><b>{{ store.stayMin }}</b>min to play</p>
        <SegBar :stops="STAY_STOPS" :value="store.stayMin" label="Minutes to play" item-class="stay-btn" @pick="(v) => store.setStay(v)" />
        <div v-if="isOutdoor" class="trip">
          <div class="trip-bar">
            <span class="go" :style="{ flex: store.travelMin }" />
            <span class="play" :style="{ flex: store.stayMin }" />
            <span class="go" :style="{ flex: store.travelMin }" />
          </div>
          <div class="trip-labels">
            <span :style="{ flex: store.travelMin }">{{ store.travelMode === 'walking' ? 'Walk' : 'Drive' }} ~{{ store.travelMin }}m</span>
            <span class="mid" :style="{ flex: store.stayMin }">Play {{ store.stayMin }}m</span>
            <span class="end" :style="{ flex: store.travelMin }">Back ~{{ store.travelMin }}m</span>
          </div>
        </div>
      </section>

      <!-- Pick a mission (at home) -->
      <section v-if="isHome" class="step">
        <div class="step-head">
          <h2><span class="num">{{ nums.mission }}</span>Pick a mission</h2>
          <span class="count">{{ fits.length }} fit</span>
        </div>
        <div class="home-list">
          <button
            v-for="m in HOME_MISSIONS"
            :key="m.id"
            class="home-item"
            :class="{ on: homePick === m.id }"
            :disabled="m.durationMin > store.stayMin"
            @click="homePick = m.id"
          >
            <span class="home-name">{{ m.title }}</span>
            <span class="home-len">{{ m.durationMin }} min</span>
            <span class="radio"><svg v-if="homePick === m.id" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></span>
          </button>
        </div>
      </section>
    </div>
    <div class="tray-space" />
  </div>

  <!-- Glass tray: who it's for, then go. -->
  <div class="tray-wrap">
    <div class="tray">
      <button class="kid-row" @click="kidOpen = true">
        <span class="kid-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4 M12 7v7 M8 10h8 M12 14l-3 6 M12 14l3 6" /></svg></span>
        <span class="kid-text">For kid · {{ kidShort }}</span>
        <span class="kid-link">Edit</span>
      </button>
      <button class="btn btn-primary cta" :disabled="!ready" @click="next">
        <span class="cta-text">{{ ctaText }}</span>
        <span class="cta-arrow"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12h14 M12.5 6l6 6-6 6" /></svg></span>
      </button>
    </div>
  </div>

  <KidSheet v-if="kidOpen" @close="kidOpen = false" />
</template>

<script setup>
// Start (iteration 3 design): first Outdoors, At home or an Indoor place,
// then only the steps that setting needs —
//   Outdoors:     where from, how far (travel minutes, walk/drive), when
//                 (hourly forecast), how long there, with the trip split
//   At home:      how long to play, then pick a home mission and play it
//   Indoor place: where from and how far, then a list of indoor places
// Where-from is browser geolocation (asked only on tap, nothing stored), a
// pilot suburb chip, or a Vicmap address from the autocomplete endpoint.
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import KidSheet from '../components/KidSheet.vue'
import { searchAddresses, getHourlyForecast } from '../api'
import { useSearchStore, TRAVEL_STOPS, STAY_STOPS } from '../store'
import { useMissionStore, HOME_MISSIONS } from '../missionStore'
import { usePreferencesStore } from '../preferencesStore'

const store = useSearchStore()
const missionStore = useMissionStore()
const prefs = usePreferencesStore()
const router = useRouter()

const HOUSE = 'M4 11 12 4.5l8 6.5 M6.5 9.5v10h11v-10 M10 19.5v-5h4v5'
const ENV = {
  outdoor: { label: 'Outdoors', icon: 'M12 3.5 6 13h3.5L7 17.5h10L14.5 13H18L12 3.5Z M12 17.5v3' },
  home: { label: 'At home', icon: HOUSE },
  indoor_place: { label: 'Indoor place', icon: 'M4.5 20V8l7.5-4 7.5 4v12 M4.5 20h15 M9 20v-5h6v5 M9 10.5h.01 M15 10.5h.01' }
}
const MODES = [
  { id: 'walking', label: 'Walk', icon: 'M13 4.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z M9.5 21l2-6 2.5 2v4 M8 11l2.5-3.5 3 1.5 2 3 M11.5 15l-1-5' },
  { id: 'driving', label: 'Drive', icon: 'M5 16.5h14v-4.2l-1.8-4.3H6.8L5 12.3v4.2Z M5 12.5h14 M7.5 16.5v2 M16.5 16.5v2' }
]
const WX_ICON = {
  sun: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z M12 2.5v2 M12 19.5v2 M2.5 12h2 M19.5 12h2 M5.3 5.3l1.4 1.4 M17.3 17.3l1.4 1.4 M5.3 18.7l1.4-1.4 M17.3 6.7l1.4-1.4',
  cloud: 'M7 18h10a4 4 0 0 0 .6-7.96A6 6 0 0 0 6.1 11.1 3.5 3.5 0 0 0 7 18Z',
  rain: 'M7 15h10a4 4 0 0 0 .6-7.96A6 6 0 0 0 6.1 8.1 3.5 3.5 0 0 0 7 15Z M9 18.5l-1 2 M13 18.5l-1 2 M17 18.5l-1 2',
  none: 'M6 12h12'
}

// Six-step segmented bar shared by "How far?" and "How long there?"; tap a
// segment or drag along it.
const SegBar = defineComponent({
  props: { stops: Array, value: Number, label: String, itemClass: String },
  emits: ['pick'],
  setup(props, { emit }) {
    let dragging = false
    const pickAt = (e) => {
      const r = e.currentTarget.getBoundingClientRect()
      if (!r.width) return
      const i = Math.max(0, Math.min(props.stops.length - 1, Math.floor(((e.clientX - r.left) / r.width) * props.stops.length)))
      if (props.stops[i] !== props.value) emit('pick', props.stops[i])
    }
    return () => h('div', {
      class: 'segbar',
      role: 'radiogroup',
      'aria-label': props.label,
      style: { gridTemplateColumns: `repeat(${props.stops.length}, minmax(0, 1fr))` },
      onPointerdown: (e) => { dragging = true; e.currentTarget.setPointerCapture?.(e.pointerId) },
      onPointermove: (e) => { if (dragging) pickAt(e) },
      onPointerup: () => { dragging = false },
      onPointercancel: () => { dragging = false }
    }, props.stops.map((n) => {
      const cur = props.stops.indexOf(props.value)
      const i = props.stops.indexOf(n)
      return h('button', {
        type: 'button',
        class: [props.itemClass, 'seg', { on: i === cur, done: i < cur }],
        role: 'radio',
        'aria-checked': i === cur,
        onClick: () => emit('pick', n)
      }, [h('span', { class: 'seg-bar' }), h('span', { class: 'seg-label' }, String(n))])
    }))
  }
})

const query = ref(store.selectedAddress?.label || store.suburb)
const open = ref(false)
const menuOpen = ref(false)
const kidOpen = ref(false)
const homePick = ref(null)
const locating = ref(false)
const locationError = ref('')
const suggestions = ref([])
const searching = ref(false)
const searchMessage = ref('')
const stripEl = ref(null)
let searchTimer = null
let searchController = null
let searchSeq = 0

const isOutdoor = computed(() => store.setting === 'outdoor')
const isHome = computed(() => store.setting === 'home')
const showFrom = computed(() => !isHome.value)
const showFar = computed(() => !isHome.value)
const showThere = computed(() => store.setting !== 'indoor_place')

// Step numbers follow whichever steps are on screen; "Where from" is 1.
const nums = computed(() => {
  let n = showFrom.value ? 1 : 0
  return {
    far: showFar.value ? ++n : 0,
    when: isOutdoor.value ? ++n : 0,
    there: showThere.value ? ++n : 0,
    mission: isHome.value ? ++n : 0
  }
})

const modeWord = computed(() => (store.travelMode === 'walking' ? 'walk' : 'drive'))
const fits = computed(() => HOME_MISSIONS.filter((m) => m.durationMin <= store.stayMin))
watch(() => store.stayMin, () => { if (!fits.value.some((m) => m.id === homePick.value)) homePick.value = null })

const pickedHome = computed(() => HOME_MISSIONS.find((m) => m.id === homePick.value) ?? null)
const ready = computed(() => (isHome.value ? !!pickedHome.value : store.hasLocation))
const ctaText = computed(() => {
  if (isHome.value) return pickedHome.value ? `Play ${pickedHome.value.title}` : 'Pick a mission'
  if (!store.hasLocation) return 'Choose a starting point'
  return store.setting === 'indoor_place' ? 'Show indoor places' : 'Show 3 ideas'
})

const kidShort = computed(() => {
  const n = prefs.likedCategories.length
  const x = prefs.excludedCategories.length
  const parts = [`${prefs.ageBand.replace('-', '–')} yrs`]
  if (n) parts.push(`${n} like${n === 1 ? '' : 's'}`)
  if (x) parts.push(`${x} not for me`)
  if (!n && !x) parts.push('no likes yet')
  return parts.join(' · ')
})

function fmt(m) {
  if (m < 60) return `${m} min`
  const hrs = Math.floor(m / 60)
  return `${hrs} hr${m % 60 ? ` ${m % 60} min` : ''}`
}

// ---- When: hourly forecast cells, today from now to 8pm, then 7am-8pm ----
const forecast = ref([])
async function loadForecast() {
  const c = store.coords
  if (!c || !isOutdoor.value) return
  try {
    forecast.value = await getHourlyForecast(c)
  } catch {
    forecast.value = []
  }
}

const WK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const hourLabel = (d) => { const hr = d.getHours(); return `${((hr + 11) % 12) + 1}${hr < 12 ? 'a' : 'p'}` }

const cells = computed(() => {
  const now = new Date()
  const byHour = new Map(forecast.value.map((f) => [f.time.toISOString().slice(0, 13), f]))
  const out = []
  for (let d = 0; d < 7; d++) {
    const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() + d)
    for (let hr = 7; hr <= 20; hr++) {
      const at = new Date(day.getFullYear(), day.getMonth(), day.getDate(), hr)
      if (d === 0 && hr <= now.getHours()) continue
      out.push(at)
    }
  }
  const first = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours())
  return [first, ...out].map((at, i, all) => {
    const f = byHour.get(at.toISOString().slice(0, 13))
    const icon = !f || f.rain == null ? 'none' : f.rain >= 60 ? 'rain' : f.rain >= 30 ? 'cloud' : 'sun'
    const newDay = i === 0 || all[i - 1].getDate() !== at.getDate()
    return {
      key: i === 0 ? 'now' : at.toISOString(),
      iso: i === 0 ? null : at.toISOString(),
      day: newDay ? (i === 0 ? 'Today' : WK[at.getDay()]) : '',
      t: i === 0 ? 'Now' : hourLabel(at),
      temp: f?.temp == null ? '–' : `${Math.round(f.temp)}°`,
      icon,
      ic: icon === 'rain' ? '#3D6E86' : icon === 'none' ? '#9AA39B' : '#C9822F',
      f
    }
  })
})

const selectedKey = computed(() => store.whenAt ?? 'now')
const selectedWx = computed(() => {
  const c = cells.value.find((x) => x.key === selectedKey.value) ?? cells.value[0]
  if (!c?.f || c.f.rain == null) return null
  return { ...c.f, icon: c.icon, wet: c.f.rain >= 60 }
})
const wxText = computed(() => {
  const w = selectedWx.value
  if (!w) return 'No forecast yet for this time'
  const base = `${Math.round(w.temp)}° · ${w.rain}% rain`
  return w.wet ? `${base} — outdoor spots may be wet` : `${base} · UV ${Math.round(w.uv ?? 0)}`
})

onMounted(() => {
  if (store.hasLocation) {
    store.loadContext()
    loadForecast()
  }
})
watch(() => store.coords, (c) => { if (c) { store.loadContext(); loadForecast() } })
watch(isOutdoor, (on) => { if (on && !forecast.value.length) loadForecast() })

// Recent suburbs first, topped up with pilot-area suburbs so the chip row is
// never empty on a fresh install.
const FALLBACK = ['Carlton North', 'Clayton', 'Glen Waverley', 'Melton', 'Caroline Springs', 'Kensington']
const quickPicks = computed(() => {
  const seen = new Set()
  return [...store.recent, ...FALLBACK].filter((s) => !seen.has(s) && seen.add(s)).slice(0, 6)
})

function pickSetting(key) {
  store.setting = key
  menuOpen.value = false
}

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
    searchMessage.value = suggestions.value.length ? '' : 'Not covered yet — try Melbourne, Monash or Melton'
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
      query.value = 'Your location'
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

// Keep the chosen forecast cell in view.
watch(selectedKey, async () => {
  await nextTick()
  stripEl.value?.querySelector('.cell.on')?.scrollIntoView?.({ inline: 'center', block: 'nearest', behavior: 'smooth' })
})

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  searchController?.abort()
})

function next() {
  if (!ready.value) return
  if (isHome.value) {
    missionStore.startHomeMission(pickedHome.value.id)
    router.push('/play/run')
    return
  }
  if (store.suburb) store.rememberSuburb(store.suburb)
  store.setTravel() // keep the radius in step with the travel choice
  store.setStay(store.stayMin) // and the requested minutes with the play time
  if (store.setting === 'indoor_place') store.searchIndoor()
  else store.fetchRecommendations()
  router.push('/play')
}
</script>

<style scoped>
.start { display: flex; flex-direction: column; gap: 12px; padding-bottom: 0; }

/* ---- header env menu ---- */
.env-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 10px 0 9px;
  border: none;
  border-radius: 999px;
  background: rgba(30, 42, 31, 0.07);
  color: var(--ink);
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}

.env-menu {
  position: absolute;
  top: 64px;
  right: 22px;
  z-index: 20;
  width: 200px;
  padding: 6px;
  border-radius: 14px;
  background: #FFFFFF;
  box-shadow: 0 10px 30px rgba(30, 42, 31, 0.18), 0 0 0 1px rgba(30, 42, 31, 0.06);
}

.env-opt {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 42px;
  padding: 0 10px;
  border: none;
  border-radius: 9px;
  background: transparent;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
}

.env-opt.on { background: rgba(47, 107, 54, 0.08); }
.env-opt-label { flex: 1; text-align: left; }

/* ---- step numbers ---- */
.num {
  flex: none;
  width: 22px;
  height: 22px;
  margin-right: 9px;
  border-radius: 50%;
  background: var(--green);
  color: #FFFFFF;
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.num.light { background: var(--paper); color: var(--green); }

/* ---- where from (green card) ---- */
.from {
  position: relative;
  flex: none;
  border-radius: 16px;
  background: var(--green);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.from-sun { position: absolute; top: 16px; right: 16px; }

.from-title {
  display: flex;
  align-items: center;
  margin: 0;
  padding-right: 36px;
  font-size: 19px;
  line-height: 1.15;
  letter-spacing: -0.3px;
  color: var(--paper);
}

.from-row { display: flex; align-items: flex-start; gap: 10px; }

.field {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 9px;
  height: 44px;
  padding: 0 14px;
  border-radius: 22px;
  background: rgba(242, 241, 236, 0.12);
  border: 1.5px solid rgba(242, 241, 236, 0.3);
}

.field.ok { border-color: rgba(180, 210, 120, 0.7); }
.field.err { border-color: #F0B27A; }

.field input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
  font-size: 14.5px;
  color: var(--paper);
}

.field input::placeholder { color: rgba(242, 241, 236, 0.6); }

.clear-btn { border: none; background: none; color: rgba(242, 241, 236, 0.75); font-size: 20px; line-height: 1; cursor: pointer; }

.use-location { flex: none; display: flex; flex-direction: column; align-items: center; gap: 3px; border: none; background: none; font-family: inherit; cursor: pointer; }
.use-location:active { transform: scale(0.95); }
.loc-circle { width: 44px; height: 44px; border-radius: 50%; background: var(--paper); display: flex; align-items: center; justify-content: center; }
.use-location.active .loc-circle { background: #B4D278; }
.loc-label { font-size: 10.5px; font-weight: 600; color: #CFE0CC; }

.spinner { width: 16px; height: 16px; border-radius: 50%; border: 2px solid rgba(47, 107, 54, 0.25); border-top-color: var(--green); animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.from-error {
  align-self: flex-start;
  margin-top: -6px;
  padding: 5px 11px;
  border-radius: 12px;
  background: #FBEFE3;
  font-size: 12px;
  font-weight: 600;
  color: #5A3410;
}

.suggest-list {
  margin-top: -6px;
  border-radius: 14px;
  background: #FFFFFF;
  box-shadow: 0 10px 24px rgba(14, 20, 15, 0.25);
  overflow: hidden;
}

.suggest-item {
  display: block;
  width: 100%;
  padding: 11px 14px;
  border: none;
  border-bottom: 1px solid var(--line);
  background: none;
  font-family: inherit;
  font-size: 13.5px;
  text-align: left;
  color: var(--ink);
  cursor: pointer;
}

.suggest-item:last-child { border-bottom: none; }
.suggest-status { padding: 11px 14px; font-size: 13px; color: var(--ink-3); }

.chips { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin: 0 -18px; padding: 0 18px; }
.chip { flex: none; padding: 7px 11px; border: none; border-radius: 10px; background: rgba(242, 241, 236, 0.14); color: var(--paper); font-family: inherit; font-size: 13px; font-weight: 600; white-space: nowrap; cursor: pointer; transition: all 0.16s ease; }
.chip.on { background: var(--paper); color: var(--green); }

.attribution { margin-top: -6px; font-size: 10.5px; color: rgba(242, 241, 236, 0.55); }
.attribution a { color: rgba(242, 241, 236, 0.75); }

/* ---- step cards ---- */
.steps { display: flex; flex-direction: column; }
.step { display: flex; flex-direction: column; gap: 14px; padding: 20px 0 22px; border-top: 1px solid rgba(30, 42, 31, 0.1); }
.step:first-child { border-top: none; }

.step-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 26px; }
.step-head h2 { display: flex; align-items: center; margin: 0; font-size: 19px; line-height: 1.15; white-space: nowrap; }

.modes { display: flex; gap: 14px; }
.mode { display: flex; align-items: center; gap: 5px; padding: 3px 0; border: none; border-bottom: 2px solid transparent; background: none; font-family: inherit; font-size: 13px; font-weight: 600; color: rgba(30, 42, 31, 0.45); cursor: pointer; }
.mode.on { color: var(--ink); border-bottom-color: var(--accent); }

.big { display: flex; align-items: baseline; gap: 8px; font-size: 14px; font-weight: 600; color: #56625A; white-space: nowrap; }
.big b { font-family: var(--font-display); font-weight: 500; font-size: 40px; line-height: 1; letter-spacing: -1.4px; color: var(--ink); }

:deep(.segbar) { display: grid; gap: 4px; touch-action: none; user-select: none; }
:deep(.seg) { display: flex; flex-direction: column; gap: 7px; padding: 0; border: none; background: none; font-family: inherit; cursor: pointer; }
:deep(.seg-bar) { height: 10px; border-radius: 5px; background: #D5E0D1; transition: background 0.2s ease; }
:deep(.seg.done .seg-bar) { background: #9EC096; }
:deep(.seg.on .seg-bar) { background: var(--green); }
:deep(.seg-label) { font-size: 12px; font-weight: 600; text-align: center; color: #56625A; }
:deep(.seg.on .seg-label) { font-weight: 700; color: var(--ink); }

.strip { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin: 0 -24px; padding: 0 24px; }
.cell {
  flex: none;
  width: 54px;
  padding: 10px 0 11px;
  border: none;
  border-radius: 14px;
  background: rgba(47, 107, 54, 0.06);
  font-family: inherit;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: background 0.16s ease;
}

.cell.on { background: var(--green); }
.cell-day { height: 11px; font-size: 9.5px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; color: var(--accent); }
.cell.on .cell-day { color: #D3E4D0; }
.cell-t { font-size: 12px; font-weight: 700; color: var(--ink); white-space: nowrap; }
.cell.on .cell-t { color: #FFFFFF; }
.cell-temp { font-size: 12px; font-weight: 600; color: #56625A; }
.cell.on .cell-temp { color: #D3E4D0; }

.wx-note { display: flex; align-items: center; gap: 7px; padding: 6px 10px; border-radius: 9px; background: rgba(47, 107, 54, 0.08); font-size: 12.5px; font-weight: 600; color: var(--green); }
.wx-note.wet { background: #E4ECF0; color: #2B4A5A; }

.outing-pill { display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; background: rgba(58, 82, 64, 0.1); font-size: 12.5px; font-weight: 600; color: #3A5240; white-space: nowrap; }

.trip { display: flex; flex-direction: column; gap: 6px; padding-top: 2px; }
.trip-bar { display: flex; gap: 3px; height: 8px; border-radius: 4px; overflow: hidden; }
.trip-bar .go { background: var(--accent); }
.trip-bar .play { background: #3A5240; }
.trip-labels { display: flex; gap: 3px; font-size: 12px; font-weight: 600; color: #56625A; }
.trip-labels span { min-width: 66px; white-space: nowrap; }
.trip-labels .mid { min-width: 0; text-align: center; color: #3A5240; }
.trip-labels .end { text-align: right; }

.count { font-size: 12.5px; font-weight: 600; color: #56625A; }

.home-list { display: flex; flex-direction: column; gap: 6px; }
.home-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 54px;
  padding: 0 14px;
  border: none;
  border-radius: 12px;
  background: rgba(47, 107, 54, 0.06);
  font-family: inherit;
  text-align: left;
  color: var(--ink);
  cursor: pointer;
  transition: all 0.16s ease;
}

.home-item:active { transform: scale(0.985); }
.home-item.on { background: var(--green); color: #FFFFFF; }
.home-item:disabled { opacity: 0.4; cursor: not-allowed; }
.home-name { flex: 1; min-width: 0; font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-len { flex: none; font-size: 12px; font-weight: 600; color: #56625A; }
.home-item.on .home-len { color: #D3E4D0; }
.radio { flex: none; width: 20px; height: 20px; border-radius: 50%; border: 1.5px solid rgba(30, 42, 31, 0.25); display: flex; align-items: center; justify-content: center; }
.home-item.on .radio { border: none; background: var(--accent); }

/* ---- glass tray ---- */
.tray-space { flex: none; height: 96px; }

.tray-wrap { position: relative; z-index: 4; margin: -110px -8px 6px; padding: 0; pointer-events: none; }
.tray {
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px) saturate(1.4);
  -webkit-backdrop-filter: blur(14px) saturate(1.4);
  box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.08), 0 8px 20px -12px rgba(30, 42, 31, 0.45);
}

.kid-row { display: flex; align-items: center; gap: 9px; height: 34px; padding: 0 6px 0 10px; border: none; background: none; font-family: inherit; color: #2E3B30; cursor: pointer; }
.kid-icon { flex: none; width: 26px; height: 26px; border-radius: 50%; background: #E3ECDF; display: flex; align-items: center; justify-content: center; }
.kid-text { flex: 1; min-width: 0; font-size: 12.5px; font-weight: 600; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kid-link { font-size: 12.5px; font-weight: 700; color: var(--green); }

.cta {
  height: 54px;
  padding: 0 9px 0 24px;
  border-radius: 999px;
  justify-content: space-between;
  box-shadow: 0 14px 28px -14px rgba(47, 107, 54, 0.75);
}

.cta:disabled { background: #CDD3CA; color: #3F4A41; box-shadow: none; cursor: not-allowed; }
.cta-text { font-size: 16.5px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cta-arrow { flex: none; width: 40px; height: 40px; border-radius: 50%; background: var(--paper); color: var(--green); display: flex; align-items: center; justify-content: center; }
.cta:disabled .cta-arrow { background: rgba(63, 74, 65, 0.12); color: #3F4A41; }
</style>
