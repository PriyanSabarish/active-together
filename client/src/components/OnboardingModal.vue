<template>
  <div class="onb" role="dialog" aria-modal="true" aria-labelledby="onb-title">
    <div class="onb-page">
      <!-- Hero: a soft landscape behind the header; fades into the paper below. -->
      <div class="hero" aria-hidden="true">
        <svg viewBox="0 0 390 238" preserveAspectRatio="xMidYMax slice">
          <rect width="390" height="238" fill="#EAF3E1" />
          <circle cx="345" cy="120" r="21" fill="#E8913A" />
          <rect x="205" y="100" width="42" height="14" rx="7" fill="#FFFFFF" opacity=".9" />
          <circle cx="241" cy="100" r="9.5" fill="#FFFFFF" opacity=".9" />
          <circle cx="263" cy="112" r="3.8" fill="#FFFFFF" opacity=".7" />
          <path d="M0 132 C60 96 124 96 184 122 C246 148 302 106 390 126 L390 238 L0 238 Z" fill="#CFE3BE" />
          <g><rect x="22.3" y="131" width="3.6" height="12" fill="#8A5A2E" /><path d="M24 104 L36 124 L12 124 Z" fill="#3A7C41" /><path d="M24 104 L36 124 L24 124 Z" fill="#2F6B36" /><path d="M24 114 L39 132 L9 132 Z" fill="#3A7C41" /><path d="M24 114 L39 132 L24 132 Z" fill="#2F6B36" /></g>
          <g><rect x="174.6" y="116" width="2.8" height="10" fill="#8A5A2E" /><path d="M176 90 L185 108 L167 108 Z" fill="#4E8F52" /><path d="M176 100 L187 117 L165 117 Z" fill="#4E8F52" /><path d="M176 100 L187 117 L176 117 Z" fill="#3A7C41" /></g>
          <g><rect x="300.3" y="135" width="3.4" height="12" fill="#8A5A2E" /><path d="M302 106 L315 128 L289 128 Z" fill="#3A7C41" /><path d="M302 106 L315 128 L302 128 Z" fill="#2F6B36" /><path d="M302 118 L318 136 L286 136 Z" fill="#3A7C41" /><path d="M302 118 L318 136 L302 136 Z" fill="#2F6B36" /></g>
          <path d="M0 176 C70 150 142 158 212 174 C282 190 332 172 390 180 L390 238 L0 238 Z" fill="#B9D9A0" />
          <g><rect x="286" y="171" width="4" height="14" fill="#754923" /><path d="M288 124 L304 156 L272 156 Z" fill="#276030" /><path d="M288 124 L304 156 L288 156 Z" fill="#1F5127" /><path d="M288 142 L307 172 L269 172 Z" fill="#276030" /><path d="M288 142 L307 172 L288 172 Z" fill="#1F5127" /></g>
          <g><rect x="345" y="179" width="3.4" height="12" fill="#754923" /><path d="M346.7 140 L360 166 L334 166 Z" fill="#276030" /><path d="M346.7 140 L360 166 L346.7 166 Z" fill="#1F5127" /><path d="M346.7 154 L363 180 L331 180 Z" fill="#276030" /><path d="M346.7 154 L363 180 L346.7 180 Z" fill="#1F5127" /></g>
          <ellipse cx="288" cy="184" rx="15" ry="3" fill="#2F6B36" opacity=".13" />
          <circle cx="252" cy="184" r="4.2" fill="#9FCC86" /><circle cx="261" cy="187" r="2.8" fill="#9FCC86" />
        </svg>
        <div class="hero-fade"></div>
      </div>

      <div class="bar">
        <div class="brand">
          <span class="pin"><span class="pin-body"></span><span class="pin-face"><i class="pin-eye"></i><i class="pin-smile"></i></span></span>
          <span class="brand-name">Active Together<span class="accent">.</span></span>
        </div>
        <button v-if="step < 4" class="skip" type="button" @click="skip">Skip</button>
      </div>

      <div class="main">
        <div class="eyebrow-row">
          <button v-if="step > 0" class="back" type="button" aria-label="Back" @click="step -= 1">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          </button>
          <span class="eyebrow">{{ copy.eb }}</span>
        </div>

        <!-- 1 · Where -->
        <div v-if="step === 0" class="card green">
          <div class="where-row">
            <div class="where-field">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F2F1EC" stroke-width="2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.6" /><path d="M15.4 15.4 21 21" /></svg>
              <span class="where-label">{{ placeLabel }}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B4D278" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5 10 17 19 7" /></svg>
            </div>
            <button type="button" class="locate" :class="{ on: usingLoc }" aria-label="Use my location" @click="locate">
              <span v-if="locating" class="spinner" />
              <svg v-else width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 3.5 3.8 10.4a.5.5 0 0 0 .04.94l6.9 2.02 2.02 6.9a.5.5 0 0 0 .94.04L20.5 3.5Z" /></svg>
            </button>
          </div>
          <p v-if="locError" class="loc-error">{{ locError }}</p>
          <div class="pop-label">Popular near you</div>
          <div class="pop-chips">
            <button v-for="n in SUBURB_CHIPS" :key="n" type="button" :class="{ on: !usingLoc && sub === n }" @click="pickSuburb(n)">{{ n }}</button>
          </div>
        </div>

        <!-- 2 · How far -->
        <div v-else-if="step === 1" class="card white">
          <div class="seg-toggle">
            <button v-for="m in MODES" :key="m.id" type="button" :class="{ on: travel === m.id }" @click="travel = m.id">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="m.icon" /></svg>{{ m.label }}
            </button>
          </div>
          <div class="big"><b>{{ farMins }}</b><span>min {{ modeWord }}, each way</span></div>
          <div class="segs" :style="{ gridTemplateColumns: `repeat(${TRAVEL_STOPS.length}, minmax(0, 1fr))` }">
            <button v-for="(n, i) in TRAVEL_STOPS" :key="n" type="button" class="seg" :class="{ on: i === far, done: i < far }" @click="far = i"><span class="seg-bar" /><span class="seg-n">{{ n }}</span></button>
          </div>
          <div class="note green-note">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.4 7-12a7 7 0 1 0-14 0c0 5.6 7 12 7 12Z" /><circle cx="12" cy="9" r="2.5" /></svg>
            {{ reachText }}
          </div>
        </div>

        <!-- 3 · When -->
        <div v-else-if="step === 2" class="card white">
          <div class="days">
            <button v-for="(d, i) in ['Today', 'Tomorrow']" :key="d" type="button" :class="{ on: day === i }" @click="pickDay(i)">{{ d }}</button>
          </div>
          <div class="big"><b>{{ whenBig }}</b><span>{{ whenSub }}</span></div>
          <div class="cells">
            <button v-for="(c, i) in cells" :key="c.key" type="button" class="cell" :class="{ on: i === cellIdx }" @click="pickCell(i)">
              <span class="cell-t">{{ c.t }}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" :stroke="i === cellIdx ? '#FFFFFF' : c.ic" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="WX_ICON[c.icon]" /></svg>
              <span class="cell-temp">{{ c.temp }}</span>
            </button>
          </div>
          <div v-if="wet" class="note wet-note">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2C5F80" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17a4 4 0 0 1-.6-7.96A6 6 0 0 1 18 9.5a3.5 3.5 0 0 1-.5 7 M8 20l1-2 M12 21l1-2 M16 20l1-2" /></svg>
            Rain likely — we'll favour covered spots.
          </div>
        </div>

        <!-- 4 · How long -->
        <div v-else-if="step === 3" class="card white">
          <div class="big"><b>{{ stayMins }}</b><span>min to play</span></div>
          <div class="segs" :style="{ gridTemplateColumns: `repeat(${STAY_STOPS.length}, minmax(0, 1fr))` }">
            <button v-for="(n, i) in STAY_STOPS" :key="n" type="button" class="seg" :class="{ on: i === stay, done: i < stay }" @click="stay = i"><span class="seg-bar" /><span class="seg-n">{{ n }}</span></button>
          </div>
          <div class="trip">
            <div class="trip-bar"><span class="go" :style="{ flex: farMins }" /><span class="play" :style="{ flex: stayMins }" /><span class="go" :style="{ flex: farMins }" /></div>
            <div class="trip-labels"><span>{{ travel === 'walking' ? 'Walk' : 'Drive' }} ~{{ farMins }}m</span><span class="mid">Play {{ stayMins }}m</span><span class="end">Back ~{{ farMins }}m</span></div>
          </div>
          <div class="note green-note">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></svg>
            Whole outing about {{ farMins * 2 + stayMins }} min
          </div>
        </div>

        <!-- 5 · All set -->
        <div v-else class="card white recap">
          <button v-for="(r, i) in recap" :key="r.k" type="button" class="recap-row" :class="{ first: i === 0 }" @click="step = i">
            <span class="tick"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5 10 17 19 7" /></svg></span>
            <span class="recap-text"><span class="recap-k">{{ r.k }}</span><span class="recap-v">{{ r.v }}</span></span>
            <span class="recap-edit">Edit</span>
          </button>
        </div>
      </div>

      <div class="text">
        <div class="mascot-box" aria-hidden="true">
          <!-- per-step props -->
          <template v-if="step === 0">
            <svg class="p-trail" width="90" height="80" viewBox="0 0 90 80" fill="none"><path d="M2 70 C 20 60, 12 44, 30 38 S 50 32, 44 18" stroke="#2F6B36" stroke-width="3" stroke-linecap="round" stroke-dasharray="1 8" /></svg>
            <svg class="p-tree-a" width="24" height="29" viewBox="0 0 24 29"><path d="M12 1 18 11H14.5L20 20H4l5.5-9H6Z" fill="#2F6B36" stroke="#2F6B36" stroke-width="1.5" stroke-linejoin="round" /><rect x="10" y="20" width="4" height="8" rx="1.5" fill="#2F6B36" /></svg>
            <svg class="p-tree-b" width="19" height="23" viewBox="0 0 19 23"><path d="M9.5 1 13.5 8H11L15 15H4l4-7H5.5Z" fill="#2F6B36" stroke="#2F6B36" stroke-width="1.5" stroke-linejoin="round" /><rect x="7.7" y="15" width="3.6" height="6" rx="1.3" fill="#2F6B36" /></svg>
          </template>
          <template v-else-if="step === 1">
            <svg class="p-flag-a" width="26" height="30" viewBox="0 0 26 30" fill="none" stroke="#E8913A" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M4 29V2" /><path d="M4 3 20 8 4 13Z" fill="#E8913A" /></svg>
            <svg class="p-flag-b" width="20" height="24" viewBox="0 0 20 24" fill="none" stroke="#2F6B36" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M4 23V2" /><path d="M4 3 16 7 4 11Z" fill="#2F6B36" /></svg>
          </template>
          <template v-else-if="step === 2">
            <svg class="p-cal" width="20" height="18" viewBox="0 0 20 18"><rect x="1" y="3" width="18" height="14" rx="4" fill="#E8913A" stroke="#E8913A" stroke-width="1.5" /><path d="M1 8h18" stroke="#FFFFFF" stroke-width="1.5" /><path d="M6 1v4 M14 1v4" stroke="#1E2A1F" stroke-width="2" stroke-linecap="round" /></svg>
          </template>
          <template v-else-if="step === 3">
            <svg class="p-heart" width="24" height="22" viewBox="0 0 24 22"><path d="M12 20.5S2 14.6 2 7.5C2 3.6 5 1 8.3 1.6c1.7.3 3 1.5 3.7 3 .7-1.5 2-2.7 3.7-3C19 1 22 3.6 22 7.5c0 7.1-10 13-10 13Z" fill="#E8913A" stroke="#E8913A" stroke-width="1.5" stroke-linejoin="round" /></svg>
            <svg class="p-spark" width="18" height="18" viewBox="0 0 18 18" fill="#2F6B36"><path d="M9 0 L11 7 L18 9 L11 11 L9 18 L7 11 L0 9 L7 7 Z" /></svg>
          </template>
          <i class="twinkle t1"></i><i class="twinkle t2"></i><i class="twinkle t3"></i>
          <div class="shadow"></div>
          <div class="mascot">
            <template v-if="step === 1">
              <i class="car"></i><i class="wheel w1"></i><i class="wheel w2"></i>
            </template>
            <i class="mascot-body"></i>
            <svg v-if="step === 2" class="dumbbell" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#1E2A1F" stroke-width="2.4" stroke-linecap="round"><path d="M4 12h16" /><circle cx="4" cy="12" r="3.4" fill="#1E2A1F" /><circle cx="20" cy="12" r="3.4" fill="#1E2A1F" /></svg>
            <span class="face">
              <span v-if="step !== 4" class="eyes"><i /><i /></span>
              <span v-else class="eyes hearts">
                <svg v-for="n in 2" :key="n" width="8" height="8" viewBox="0 0 24 22"><path d="M12 20.5S2 14.6 2 7.5C2 3.6 5 1 8.3 1.6c1.7.3 3 1.5 3.7 3 .7-1.5 2-2.7 3.7-3C19 1 22 3.6 22 7.5c0 7.1-10 13-10 13Z" fill="#1E2A1F" /></svg>
              </span>
              <span class="mouth"></span>
              <i class="cheek l"></i><i class="cheek r"></i>
            </span>
          </div>
        </div>
        <h2 id="onb-title" class="title">{{ copy.title }}</h2>
        <p class="body">{{ copy.body }}</p>
      </div>

      <div class="foot">
        <div class="dots">
          <button v-for="i in 5" :key="i" type="button" :class="{ on: i - 1 === step, past: i - 1 < step }" :aria-label="`Step ${i}`" @click="step = i - 1" />
        </div>
        <button type="button" class="cta" @click="next">
          <span class="cta-text">{{ cta }}</span>
          <span class="cta-arrow"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14 M13 6l6 6-6 6" /></svg></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Setup walkthrough, full screen over Start, shown after the cover on every
// sign-in. Four questions (where, how far, when, how long) and an "All set"
// recap, with the mascot reacting to each. Nothing is saved until the last
// button: "Let's go" writes the answers into the search store so Start opens
// already filled in; Skip leaves the store alone and Start opens in its
// guided first-run mode (store.guided) when no starting point is saved yet.
// Emits 'done' with 'setup' or 'skip'.
import { computed, onMounted, ref, watch } from 'vue'
import { getHourlyForecast } from '../api'
import { SUBURB_COORDS, TRAVEL_STOPS, STAY_STOPS, guidedStartEnabled, useSearchStore } from '../store'

const emit = defineEmits(['done'])
const store = useSearchStore()

const SUBURB_CHIPS = ['Oakleigh', 'Clayton', 'Glen Waverley', 'Carlton North', 'Kensington', 'Melton']
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
const SPEED_KMH = { walking: 5, driving: 30 }
const TOMORROW_HOURS = [9, 11, 13, 15, 17]

const COPY = [
  { eb: 'Step 1 of 4', title: 'Where are you starting?', body: 'Pick a suburb or use your location.' },
  { eb: 'Step 2 of 4', title: 'How far will you go?', body: 'Each way. Walking or driving, your call.' },
  { eb: 'Step 3 of 4', title: 'When are you heading out?', body: 'We check the weather for that time.' },
  { eb: 'Step 4 of 4', title: 'How long to play?', body: 'Time at the place, not counting travel.' },
  { eb: 'All set', title: "You're all set.", body: "We've filled in your Start screen with these. Tap any to change it." }
]

const step = ref(0)
const sub = ref(SUBURB_CHIPS.includes(store.suburb) ? store.suburb : 'Oakleigh')
const myPos = ref(store.myLocation)
const usingLoc = ref(false)
const locating = ref(false)
const locError = ref('')
const travel = ref('walking')
const far = ref(2)
const day = ref(0)
const cellIdx = ref(0)
const stay = ref(2)
const forecast = ref([])

const copy = computed(() => COPY[step.value])
const cta = computed(() => (step.value < 3 ? 'Next' : step.value === 3 ? 'Show my ideas' : "Let's go"))
const modeWord = computed(() => (travel.value === 'walking' ? 'walk' : 'drive'))
const farMins = computed(() => TRAVEL_STOPS[far.value])
const stayMins = computed(() => STAY_STOPS[stay.value])
const placeLabel = computed(() => (usingLoc.value ? 'Current location' : sub.value))
const reachText = computed(() => {
  const km = Math.round((farMins.value / 60) * SPEED_KMH[travel.value] * 10) / 10
  return `Covers about ${km} km from ${usingLoc.value ? 'you' : sub.value}`
})

// ---- where ----
function pickSuburb(n) {
  sub.value = n
  usingLoc.value = false
  locError.value = ''
}

// Geolocation is asked for only on tap. The point is kept here until the last
// button; nothing is stored or reverse geocoded.
function locate() {
  if (locating.value) return
  if (usingLoc.value) {
    usingLoc.value = false
    return
  }
  locError.value = ''
  if (!('geolocation' in navigator)) {
    locError.value = 'Location is not available in this browser. Pick a suburb instead.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      locating.value = false
      myPos.value = { latitude: pos.coords.latitude, longitude: pos.coords.longitude }
      usingLoc.value = true
    },
    (err) => {
      locating.value = false
      locError.value = err.code === err.PERMISSION_DENIED
        ? 'Location permission was denied. Pick a suburb instead.'
        : 'We could not get your location. Pick a suburb instead.'
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
  )
}

const coords = computed(() => (usingLoc.value ? myPos.value : SUBURB_COORDS[sub.value] ?? null))

// ---- when ----
async function loadForecast() {
  const c = coords.value
  if (!c) { forecast.value = []; return }
  try {
    forecast.value = await getHourlyForecast(c)
  } catch {
    forecast.value = []
  }
}
onMounted(loadForecast)
watch(coords, loadForecast)

const hourKey = (d) => d.toISOString().slice(0, 13)
const hourLabel = (hr) => `${((hr + 11) % 12) + 1}${hr < 12 ? 'am' : 'pm'}`
const slots = computed(() => {
  const now = new Date()
  if (day.value === 0) {
    const out = [{ at: null, label: 'Now', iso: null }]
    for (let hr = now.getHours() + 1; hr <= 20 && out.length < 5; hr++) {
      const at = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hr)
      out.push({ at, label: hourLabel(hr), iso: at.toISOString() })
    }
    return out
  }
  return TOMORROW_HOURS.map((hr) => {
    const at = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, hr)
    return { at, label: hourLabel(hr), iso: at.toISOString() }
  })
})
const cells = computed(() => {
  const byHour = new Map(forecast.value.map((f) => [hourKey(f.time), f]))
  return slots.value.map((s) => {
    const f = byHour.get(hourKey(s.at ?? new Date()))
    const icon = !f || f.rain == null ? 'none' : f.rain >= 60 ? 'rain' : f.rain >= 30 ? 'cloud' : 'sun'
    return {
      key: s.label,
      t: s.label,
      temp: f?.temp == null ? '–' : `${Math.round(f.temp)}°`,
      icon,
      ic: icon === 'rain' ? '#3D6E86' : icon === 'none' ? '#9AA39B' : '#E8913A',
      iso: s.iso,
      f
    }
  })
})
const cur = computed(() => cells.value[cellIdx.value] ?? cells.value[0])
const wet = computed(() => (cur.value?.f?.rain ?? 0) >= 60)
const whenBig = computed(() => cur.value?.t ?? 'Now')
const whenSub = computed(() => `${day.value ? 'tomorrow' : 'today'}${cur.value?.f?.temp != null ? ` · ${Math.round(cur.value.f.temp)}°` : ''}`)

function pickDay(i) {
  day.value = i
  cellIdx.value = 0
}
function pickCell(i) {
  cellIdx.value = i
}

// ---- recap + finish ----
const recap = computed(() => [
  { k: 'Starting from', v: placeLabel.value },
  { k: 'How far', v: `${farMins.value} min ${modeWord.value}, each way` },
  { k: 'When', v: `${whenBig.value} ${day.value ? 'tomorrow' : 'today'}${cur.value?.f?.temp != null ? ` · ${Math.round(cur.value.f.temp)}°` : ''}` },
  { k: 'How long', v: `${stayMins.value} min to play` }
])

function next() {
  if (step.value < 4) {
    step.value += 1
    return
  }
  apply()
  emit('done', 'setup')
}

function apply() {
  store.setting = 'outdoor'
  if (usingLoc.value && myPos.value) {
    store.setMyLocation(myPos.value)
  } else {
    store.suburb = sub.value
    store.selectedAddress = null
    store.useMyLocation = false
    store.rememberSuburb(sub.value)
  }
  store.setTravel({ minutes: farMins.value, mode: travel.value })
  store.setStay(stayMins.value)
  store.whenAt = cur.value?.iso ?? null
  store.guided = false
}

// Skip leaves everything as it was. A first-time user (no saved starting
// point) lands on the guided Start; a returning one just sees theirs.
function skip() {
  store.guided = guidedStartEnabled() && !store.hasLocation
  emit('done', 'skip')
}
</script>

<style scoped>
.onb {
  position: absolute;
  inset: 0;
  z-index: 1100; /* above Leaflet panes and controls (up to 1000) */
  background: var(--paper);
  overflow-x: hidden;
  overflow-y: auto;
  font-family: var(--font-body);
}

.onb-page {
  position: relative;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 58px 0 max(26px, calc(env(safe-area-inset-bottom, 0px) + 18px));
}

.hero { position: absolute; top: 0; left: 0; right: 0; height: 238px; overflow: hidden; z-index: 0; }
.hero svg { width: 100%; height: 100%; display: block; }
.hero-fade { position: absolute; left: 0; right: 0; bottom: 0; height: 70px; background: linear-gradient(180deg, rgba(242, 241, 236, 0), #F2F1EC); }

/* header */
.bar { position: relative; z-index: 1; display: flex; align-items: center; justify-content: space-between; padding: 0 20px 6px 24px; }
.brand { display: flex; align-items: center; gap: 9px; }
.brand-name { font-family: var(--font-display); font-weight: 600; font-size: 17px; letter-spacing: -0.3px; color: var(--ink); }
.accent { color: var(--accent); }
.pin { position: relative; width: 24px; height: 30px; }
.pin-body { position: absolute; top: 0; left: 0; width: 24px; height: 24px; background: var(--green); border-radius: 50% 50% 3px 50%; transform: rotate(45deg); }
.pin-face { position: absolute; top: 5px; left: 5px; width: 14px; height: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; }
.pin-eye { width: 5px; height: 5px; border-radius: 50%; background: var(--accent); }
.pin-smile { width: 9px; height: 4px; border-bottom: 1.5px solid var(--paper); border-radius: 0 0 9px 9px; }
.skip {
  height: 34px; padding: 0 14px; border: none; border-radius: 999px; background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.06);
  font-family: inherit; font-size: 13px; font-weight: 700; color: #3F4A41; cursor: pointer;
}

/* card area */
.main { position: relative; z-index: 1; flex: none; display: flex; flex-direction: column; padding: clamp(24px, 7vh, 62px) 18px 0; }
.eyebrow-row { display: flex; align-items: center; gap: 8px; margin: 0 0 10px 4px; }
.back { width: 28px; height: 28px; border: none; border-radius: 50%; background: rgba(255, 255, 255, 0.75); box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.06); display: flex; align-items: center; justify-content: center; cursor: pointer; }
.eyebrow { height: 28px; padding: 0 12px; border-radius: 999px; display: flex; align-items: center; background: rgba(255, 255, 255, 0.75); box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.06); font-size: 12px; font-weight: 700; letter-spacing: 0.4px; color: var(--green); }

.card { border-radius: 26px; padding: 18px; display: flex; flex-direction: column; gap: 14px; }
.card.green { background: var(--green); box-shadow: 0 18px 32px -18px rgba(47, 107, 54, 0.85); }
.card.white { background: #FFFFFF; box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.06), 0 14px 30px -20px rgba(30, 42, 31, 0.35); }

/* step 1 */
.where-row { display: flex; align-items: center; gap: 10px; }
.where-field { flex: 1; min-width: 0; height: 48px; box-sizing: border-box; padding: 0 14px; border-radius: 999px; background: rgba(242, 241, 236, 0.12); border: 1.5px solid rgba(242, 241, 236, 0.35); display: flex; align-items: center; gap: 9px; }
.where-label { flex: 1; min-width: 0; font-size: 15px; font-weight: 600; color: var(--paper); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.locate { flex: none; width: 48px; height: 48px; border: none; border-radius: 50%; background: var(--paper); color: var(--green); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.16s ease; }
.locate.on { background: #B4D278; color: var(--ink); }
.locate:active { transform: scale(0.94); }
.spinner { width: 16px; height: 16px; border-radius: 50%; border: 2px solid rgba(47, 107, 54, 0.25); border-top-color: var(--green); animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loc-error { margin: -4px 0 0; align-self: flex-start; padding: 5px 11px; border-radius: 12px; background: #FBEFE3; font-size: 12px; font-weight: 600; color: #5A3410; }
.pop-label { font-size: 12px; font-weight: 700; letter-spacing: 0.4px; color: #CFE0CC; }
.pop-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.pop-chips button { padding: 8px 12px; border: none; border-radius: 10px; background: rgba(242, 241, 236, 0.12); color: rgba(242, 241, 236, 0.85); font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.16s ease; }
.pop-chips button.on { background: var(--paper); color: var(--green); font-weight: 700; }

/* shared big number + segmented bar */
.big { display: flex; align-items: baseline; gap: 8px; }
.big b { font-family: var(--font-display); font-weight: 600; font-size: 44px; line-height: 1; letter-spacing: -1.6px; color: var(--ink); }
.big span { font-size: 14px; font-weight: 600; color: #56625A; white-space: nowrap; }
.segs { display: grid; gap: 4px; }
.seg { display: flex; flex-direction: column; gap: 7px; padding: 6px 0; border: none; background: none; font-family: inherit; cursor: pointer; }
.seg-bar { height: 12px; border-radius: 6px; background: #E6E5DD; transition: background 0.2s ease; }
.seg.done .seg-bar { background: #B9D9A0; }
.seg.on .seg-bar { background: var(--green); }
.seg-n { font-size: 12px; font-weight: 600; text-align: center; color: #6B756D; }
.seg.on .seg-n { font-weight: 700; color: var(--ink); }

.note { display: flex; align-items: center; gap: 7px; padding: 8px 11px; border-radius: 12px; font-size: 12.5px; font-weight: 600; }
.note svg { flex: none; }
.green-note { background: #E3ECDF; color: var(--green); }
.wet-note { background: #DCEAF3; color: #173246; }

/* step 2 */
.seg-toggle { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 4px; padding: 4px; border-radius: 999px; background: var(--paper); }
.seg-toggle button { height: 38px; border: none; border-radius: 999px; display: flex; align-items: center; justify-content: center; gap: 7px; background: transparent; color: #6B756D; font-family: inherit; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.16s ease; }
.seg-toggle button.on { background: #FFFFFF; color: var(--green); font-weight: 700; box-shadow: 0 1px 3px rgba(30, 42, 31, 0.12); }

/* step 3 */
.days { display: flex; gap: 6px; }
.days button { padding: 8px 13px; border: none; border-radius: 999px; background: var(--paper); color: #3F4A41; font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.16s ease; }
.days button.on { background: var(--green); color: var(--paper); font-weight: 700; }
.cells { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 5px; }
.cell { padding: 10px 0 11px; border: none; border-radius: 14px; display: flex; flex-direction: column; align-items: center; gap: 6px; background: var(--paper); font-family: inherit; cursor: pointer; transition: background 0.16s ease; }
.cell.on { background: var(--green); }
.cell-t { font-size: 12px; font-weight: 700; color: var(--ink); white-space: nowrap; }
.cell-temp { font-size: 12px; font-weight: 600; color: #6B756D; }
.cell.on .cell-t { color: #FFFFFF; }
.cell.on .cell-temp { color: #CFE0CC; }

/* step 4 */
.trip { display: flex; flex-direction: column; gap: 7px; padding-top: 2px; }
.trip-bar { display: flex; gap: 3px; height: 9px; border-radius: 5px; overflow: hidden; }
.trip-bar .go { background: var(--accent); }
.trip-bar .play { background: var(--green); }
.trip-labels { display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: #56625A; }
.trip-labels .mid { color: var(--green); }

/* step 5 */
.card.recap { padding: 4px 16px; gap: 0; }
.recap-row { display: flex; align-items: center; gap: 12px; padding: 13px 0; border: none; border-top: 1px solid rgba(30, 42, 31, 0.07); background: none; font-family: inherit; text-align: left; cursor: pointer; }
.recap-row.first { border-top: none; }
.tick { flex: none; width: 28px; height: 28px; border-radius: 50%; background: var(--green); display: flex; align-items: center; justify-content: center; }
.recap-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.recap-k { font-size: 12px; font-weight: 600; color: #6B756D; }
.recap-v { margin-top: 2px; font-size: 16px; font-weight: 700; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recap-edit { flex: none; height: 30px; padding: 0 12px; border-radius: 999px; background: var(--paper); color: var(--green); font-size: 12.5px; font-weight: 700; display: flex; align-items: center; }

/* mascot + copy */
.text { position: relative; z-index: 1; flex: none; padding: 26px 24px 0; }
.mascot-box { position: relative; width: 84px; height: 76px; margin-bottom: 10px; }
.mascot-box > svg { position: absolute; }
.p-trail { top: -4px; left: -5px; }
.p-tree-a { bottom: -6px; left: -6px; }
.p-tree-b { top: -6px; right: -2px; }
.p-flag-a { bottom: -4px; left: -6px; }
.p-flag-b { top: -6px; right: -2px; }
.p-cal { top: -4px; right: -2px; }
.p-heart { bottom: -2px; left: -6px; }
.p-spark { top: -4px; right: 0; }
.twinkle { position: absolute; border-radius: 50%; animation: twinkle 2.2s ease-in-out infinite; }
.twinkle.t1 { top: 3px; left: 0; width: 7px; height: 7px; background: var(--accent); }
.twinkle.t2 { top: 34px; left: 72px; width: 5px; height: 5px; background: var(--green); animation-duration: 2.6s; animation-delay: 0.4s; }
.twinkle.t3 { top: 2px; left: 70px; width: 6px; height: 6px; background: var(--green); opacity: 0.35; animation-duration: 2s; animation-delay: 0.8s; }
@keyframes twinkle { 0%, 100% { opacity: 0.25; transform: scale(0.8); } 50% { opacity: 0.9; transform: scale(1.15); } }
.shadow { position: absolute; bottom: 2px; left: 13px; width: 44px; height: 9px; border-radius: 50%; background: rgba(30, 42, 31, 0.1); }
.mascot { position: relative; width: 58px; height: 64px; margin: 0 auto; animation: float 3.2s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0) rotate(-4deg); } 50% { transform: translateY(-7px) rotate(4deg); } }
.mascot-body { position: absolute; top: 0; left: 2px; width: 52px; height: 52px; background: var(--green); border-radius: 50% 50% 6px 50%; transform: rotate(45deg); }
.car { position: absolute; bottom: -4px; left: 4px; width: 50px; height: 16px; border-radius: 6px; background: var(--accent); }
.wheel { position: absolute; bottom: -9px; width: 12px; height: 12px; border-radius: 50%; background: var(--ink); }
.wheel.w1 { left: 9px; }
.wheel.w2 { left: 37px; }
.dumbbell { position: absolute; bottom: 2px; left: -22px; }
.face { position: absolute; top: 11px; left: 13px; width: 30px; height: 28px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
.eyes { display: flex; gap: 8px; }
.eyes i { width: 5.5px; height: 5.5px; border-radius: 50%; background: var(--ink); }
.eyes.hearts { gap: 6px; }
.mouth { width: 15px; height: 7.5px; border-radius: 0 0 15px 15px; border-bottom: 2.2px solid var(--paper); }
.cheek { position: absolute; top: 11px; width: 6px; height: 4px; border-radius: 50%; background: var(--accent); opacity: 0.55; }
.cheek.l { left: -2px; }
.cheek.r { right: -2px; }

.title { margin: 0 0 8px; font-family: var(--font-display); font-weight: 700; font-size: 32px; line-height: 1.02; letter-spacing: -0.8px; color: var(--ink); text-wrap: pretty; }
.body { margin: 0; font-size: 15.5px; line-height: 1.45; color: #5A645C; text-wrap: pretty; }

/* footer: dots + button */
.foot { position: relative; z-index: 1; margin-top: auto; padding: 18px 14px 0; display: flex; flex-direction: column; gap: 14px; }
.dots { display: flex; gap: 6px; padding-left: 10px; }
.dots button { width: 7px; height: 7px; padding: 0; border: none; border-radius: 999px; background: rgba(30, 42, 31, 0.18); cursor: pointer; transition: all 0.3s ease; }
.dots button.past { background: #B9D9A0; }
.dots button.on { width: 26px; background: var(--green); }
.cta { display: flex; align-items: center; justify-content: space-between; height: 58px; padding: 0 9px 0 24px; border: none; border-radius: 999px; background: var(--green); color: var(--paper); font-family: inherit; box-shadow: 0 14px 28px -14px rgba(47, 107, 54, 0.75); cursor: pointer; }
.cta:active { transform: scale(0.985); }
.cta-text { font-size: 16.5px; font-weight: 700; }
.cta-arrow { width: 40px; height: 40px; border-radius: 50%; background: var(--paper); display: flex; align-items: center; justify-content: center; }

@media (prefers-reduced-motion: reduce) {
  .mascot, .twinkle { animation: none; }
}
</style>
