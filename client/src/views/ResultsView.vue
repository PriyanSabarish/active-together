<template>
  <AppHeader />

  <!-- First run: nothing to show until a starting point exists. -->
  <div v-if="!store.hasLocation" class="scroll-area setup">
    <span class="setup-glyph">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <circle cx="12" cy="12" r="7" /><circle cx="12" cy="12" r="2.2" fill="currentColor" stroke="none" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
      </svg>
    </span>
    <h1>Set up where you're starting</h1>
    <p class="subtitle">We need a starting point and how long you've got before we can suggest anything nearby.</p>
    <button class="btn btn-primary setup-cta" @click="$router.push('/')">Set up now <span class="btn-arrow">→</span></button>
  </div>

  <!-- Indoor place (story 9.3): an unverified list, no missions. -->
  <IndoorList v-else-if="store.setting === 'indoor_place'" />

  <div v-else class="scroll-area">
    <!-- A mission is running: offer to go back to it before anything else. -->
    <button v-if="missionStore.status === 'in_progress'" class="resume" @click="$router.push('/play/run')">
      <span class="resume-text"><b>{{ missionStore.active.title }}</b> · task {{ missionStore.stepIndex + 1 }} of {{ missionStore.totalSteps }}</span>
      <span class="resume-go">Continue →</span>
    </button>

    <h1>Your top options</h1>
    <p class="subtitle">Each one now comes with a mission for your kid.</p>

    <!-- Gap 2 — the current window, and a way to change it without redoing setup. -->
    <div class="window-row">
      <span class="window-text">{{ windowLabel }}</span>
      <button class="pill adjust-btn" @click="openAdjust">Adjust</button>
    </div>

    <!-- loading: three skeleton cards while /recommendations is in flight -->
    <template v-if="store.loading">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <div class="sk-row">
          <span class="sk-circle" />
          <span class="sk-lines"><span class="sk-line w60" /><span class="sk-line w40" /></span>
          <span class="sk-pill" />
        </div>
        <span class="sk-block" />
      </div>
      <p class="loading-note">Checking places and today's forecast…</p>
    </template>

    <!-- backend / network error -->
    <template v-else-if="store.status === 'error'">
      <div class="empty-state">
        <span class="empty-glyph">!</span>
        <p class="empty-title">We couldn't load places</p>
        <p class="empty-text">{{ store.error }}</p>
        <button class="btn btn-primary widen-btn" @click="store.fetchRecommendations()">Try again</button>
      </div>
    </template>

    <!-- outside the pilot area -->
    <template v-else-if="store.status === 'out_of_bounds'">
      <div class="empty-state">
        <span class="empty-glyph">×</span>
        <p class="empty-title">Outside the pilot area</p>
        <p class="empty-text">
          {{ store.message || 'Selected location is outside the active pilot area.' }}
          Active Together currently covers the City of Melbourne, Monash and Melton.
        </p>
        <button class="btn btn-primary widen-btn" @click="$router.push('/')">Change location</button>
      </div>
    </template>

    <!-- zero results -->
    <template v-else-if="store.results.length === 0">
      <div class="empty-state">
        <span class="empty-glyph">?</span>
        <template v-if="store.moreTime">
          <p class="empty-title">Not enough time for the trip</p>
          <p class="empty-text">
            Nothing fits in a {{ store.outingMin }} minute outing once travel there and back is counted.
            About {{ store.moreTime.total_min }} minutes would fit
            {{ store.moreTime.fits_count === 1 ? '1 place' : `${store.moreTime.fits_count} places` }}.
          </p>
          <button class="btn btn-primary widen-btn" @click="allowMoreTime">
            Allow {{ store.moreTime.total_min }} minutes
          </button>
        </template>
        <template v-else>
          <p class="empty-title">Nothing within {{ store.radiusKm }} km</p>
          <p class="empty-text">
            {{ store.message || `We couldn't find activity places within ${store.radiusKm} km of ${store.locationLabel}.` }}
            <template v-if="store.radiusKm < 10">Try a wider search radius.</template>
          </p>
          <button v-if="store.radiusKm < 10" class="btn btn-primary widen-btn" @click="widen">
            Search {{ nextRadius }} km instead
          </button>
        </template>
      </div>
    </template>

    <!-- results: map with a numbered pin per place, then one card per place -->
    <template v-else>
      <PlaceMap
        class="results-map"
        :center="store.coords"
        :places="store.results"
        fit
        numbered
        you-chip
        height="150px"
        @select="openById"
      />

      <article
        v-for="place in store.results"
        :key="place.id"
        class="result-card"
        role="button"
        tabindex="0"
        @click="open(place)"
        @keydown.enter="open(place)"
      >
        <div class="card-top">
          <CategoryIcon :category="place.category" />
          <div class="card-title">
            <p class="place-name" :class="{ unnamed: place.unnamed }">{{ place.name }}</p>
            <p class="place-meta">{{ place.categoryLabel }} · {{ place.distanceKm }} km</p>
          </div>
          <ConditionBadge :badge="place.badge" />
        </div>
        <div class="card-foot">
          <!-- Mission count is mock until the missions endpoint is wired (see MOCK_MISSIONS). -->
          <span class="badge mission">{{ missionFor(place).steps }}-task mission</span>
          <span v-if="justAdjusted" class="updated-tag">Updated to fit new window</span>
        </div>
      </article>

      <p v-if="store.results.length === 1" class="footnote">
        Only one place within {{ store.radiusKm }} km of {{ store.locationLabel }}.
        <template v-if="store.radiusKm < 10">Widen the radius to see more options.</template>
      </p>
      <p v-else-if="store.results.length === 2" class="footnote">
        Only two places within {{ store.radiusKm }} km of {{ store.locationLabel }}.
      </p>
    </template>
  </div>

  <!-- Adjust sheet: bottom sheet over the list; z-index sits above Leaflet panes. -->
  <div v-if="adjusting" class="sheet-backdrop" @click.self="adjusting = false">
    <div class="sheet" role="dialog" aria-label="Adjust search">
      <h2>Adjust search</h2>

      <p class="section-label" style="margin-top: 16px">How far, each way</p>
      <div class="seg-row">
        <button v-for="m in MODES" :key="m.id" class="seg-btn" :class="{ on: draft.travelMode === m.id }" @click="draft.travelMode = m.id">{{ m.label }}</button>
      </div>
      <div class="seg-row" style="margin-top: 8px">
        <button v-for="n in TRAVEL_STOPS" :key="n" class="seg-btn mins-btn" :class="{ on: draft.travelMin === n }" @click="draft.travelMin = n">{{ n }}</button>
      </div>

      <p class="section-label" style="margin-top: 18px">How long to play</p>
      <div class="seg-row">
        <button v-for="n in STAY_STOPS" :key="n" class="seg-btn mins-btn" :class="{ on: draft.durationMin === n }" @click="draft.durationMin = n">{{ n }}</button>
      </div>

      <div class="btn-row" style="margin-top: 18px">
        <button class="btn btn-secondary" @click="adjusting = false">Cancel</button>
        <button class="btn btn-primary" @click="applyAdjust">Apply</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Play tab root: your top options for the current window (place + radius +
// duration), from POST /recommendations. With no starting point yet it shows
// the first-run setup card instead (routes into Start). Handles loading,
// error, out-of-pilot-area and zero-result states. The Adjust sheet changes
// travel time and play time in place and refetches; the starting point itself is
// changed on Start. A running mission gets a resume banner at the top.
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CategoryIcon from '../components/CategoryIcon.vue'
import ConditionBadge from '../components/ConditionBadge.vue'
import PlaceMap from '../components/PlaceMap.vue'
import IndoorList from '../components/IndoorList.vue'
import { useSearchStore, TRAVEL_STOPS, STAY_STOPS } from '../store'
import { useMissionStore } from '../missionStore'

const store = useSearchStore()
const missionStore = useMissionStore()
const router = useRouter()

// Landing here directly (e.g. page refresh) still runs the search.
if (!store.loading && store.status === 'idle') store.fetchRecommendations()

// Mock mission per place until F14 (mission store) lands — deterministic by
// place id so the badge doesn't change between re-renders.
const MOCK_MISSIONS = [
  { steps: 3, title: 'Bark Detective', blurb: 'find, feel and compare three kinds of tree bark.' },
  { steps: 2, title: 'Shadow Tag', blurb: "chase and copy each other's shadow shapes." },
  { steps: 2, title: 'Cloud Spotting', blurb: 'name the shapes you find in the clouds.' },
  { steps: 3, title: 'Colour Hunt', blurb: 'find one thing in five different colours.' }
]

function missionFor(place) {
  let hash = 0
  for (const ch of String(place.id)) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return MOCK_MISSIONS[hash % MOCK_MISSIONS.length]
}

const nextRadius = computed(() => (store.radiusKm === 3 ? 5 : 10))

// Gap 2 — adjust travel and play time in place, with the same choices as
// Start. Location is left alone; that still goes through Start.
const MODES = [{ id: 'walking', label: 'Walk' }, { id: 'driving', label: 'Drive' }]
const adjusting = ref(false)
const justAdjusted = ref(false)
const draft = reactive({ travelMode: store.travelMode, travelMin: store.travelMin, durationMin: store.stayMin })

// Same words as Start: travel each way and time to play, not km.
const windowLabel = computed(() =>
  `${store.travelMode === 'walking' ? 'Walk' : 'Drive'} ${store.travelMin} min · ${store.stayMin} min to play`
)

function openAdjust() {
  draft.travelMode = store.travelMode
  draft.travelMin = store.travelMin
  draft.durationMin = store.stayMin
  adjusting.value = true
}

function applyAdjust() {
  const changed = draft.travelMode !== store.travelMode || draft.travelMin !== store.travelMin || draft.durationMin !== store.stayMin
  store.setTravel({ minutes: draft.travelMin, mode: draft.travelMode })
  store.setStay(draft.durationMin)
  adjusting.value = false
  if (!changed) return
  justAdjusted.value = true
  store.fetchRecommendations()
}

// Raise the play time until the whole outing reaches the suggested total, using
// the same play-time steps the Start screen offers, then search again.
function allowMoreTime() {
  const needed = store.moreTime.total_min - store.travelMin * 2
  const stay = STAY_STOPS.find((m) => m >= needed) ?? STAY_STOPS[STAY_STOPS.length - 1]
  store.setStay(Math.max(stay, store.stayMin))
  store.fetchRecommendations()
}

function widen() {
  store.radiusKm = nextRadius.value
  store.fetchRecommendations()
}

function open(place) {
  router.push(`/play/place/${place.id}`)
}

function openById(id) {
  router.push(`/play/place/${id}`)
}
</script>

<style scoped>
.setup { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 0 28px; }
.setup-glyph { width: 64px; height: 64px; border-radius: 50%; background: var(--green-light); color: var(--green); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 18px; }
.setup h1 { text-wrap: balance; }
.setup-cta { width: 100%; margin-top: 22px; }

.resume {
  width: 100%;
  margin-bottom: 14px;
  padding: 11px 14px;
  border: none;
  border-radius: var(--radius-field);
  background: var(--dark);
  color: var(--paper);
  font-family: inherit;
  font-size: 13.5px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
}

.resume b { font-weight: 700; }
.resume-go { color: var(--accent); font-weight: 700; white-space: nowrap; }


.card-foot { margin-top: 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.window-row {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.window-text { font-family: var(--font-display); font-size: 16px; font-weight: 600; letter-spacing: -0.2px; }
.adjust-btn { background: var(--green-light); color: var(--green-dark); box-shadow: none; }

.updated-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--amber-light);
  color: var(--amber);
  font-size: 12px;
  font-weight: 600;
}

/* adjust sheet */
.sheet-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(30, 42, 31, 0.45);
  display: flex;
  align-items: flex-end;
  z-index: 1000; /* above Leaflet panes */
}

.sheet {
  width: 100%;
  background: var(--paper);
  border-radius: 24px 24px 0 0;
  padding: 22px 24px calc(22px + env(safe-area-inset-bottom, 0px));
  box-shadow: 0 -10px 30px rgba(30, 42, 31, 0.18);
}



.results-map { margin-top: 16px; }

.result-card {
  position: relative;
  margin-top: 12px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 15px 16px 14px;
  cursor: pointer;
  transition: box-shadow 0.12s ease, transform 0.12s ease;
}

.result-card:hover { box-shadow: var(--shadow-raised); }
.result-card:active { transform: scale(0.985); }

.card-top { display: flex; align-items: center; gap: 12px; }
.card-title { flex: 1; min-width: 0; }

.place-name { font-family: var(--font-display); font-size: 17px; font-weight: 600; letter-spacing: -0.2px; }
.place-meta { font-size: 13px; color: var(--ink-3); margin-top: 2px; }


.footnote {
  text-align: center;
  font-size: 12px;
  color: var(--ink-4);
  margin-top: 20px;
  line-height: 1.5;
}

/* skeleton */
.skeleton-card {
  margin-top: 12px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 16px;
}

.sk-row { display: flex; align-items: center; gap: 12px; }

.sk-circle, .sk-line, .sk-pill, .sk-block {
  background: var(--tint);
  animation: pulse 1.2s ease-in-out infinite;
  display: block;
}

.sk-circle { width: 32px; height: 32px; border-radius: 50%; }
.sk-lines { flex: 1; display: flex; flex-direction: column; gap: 7px; }
.sk-line { height: 10px; border-radius: 5px; }
.w60 { width: 60%; }
.w40 { width: 40%; }
.sk-pill { width: 64px; height: 22px; border-radius: 11px; }
.sk-block { margin-top: 14px; height: 64px; border-radius: 13px; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}

.loading-note { text-align: center; font-size: 12.5px; color: var(--ink-4); margin-top: 18px; }

/* empty */
.empty-state {
  margin-top: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 24px;
}

.empty-glyph {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--tint);
  color: var(--ink-4);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.empty-title { font-family: var(--font-display); font-size: 19px; font-weight: 600; margin-top: 16px; }
.empty-text { font-size: 13.5px; color: var(--ink-3); line-height: 1.5; margin-top: 8px; }
.widen-btn { margin-top: 20px; height: 48px; }
</style>
