<template>
  <AppHeader />

  <div class="scroll-area">
    <button class="pill crumb" @click="$router.push('/location')">‹ Change starting point</button>
    <div class="head-row">
      <div>
        <h1>Your top options</h1>
        <p class="subtitle">Each one now comes with a mission for Daniel.</p>
      </div>
    </div>

    <!-- Gap 2 — the current window, and a way to change it without redoing setup. -->
    <div class="window-row">
      <span class="window-text">{{ store.radiusKm }} km · {{ store.planMin }} min</span>
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
        <button class="btn btn-primary widen-btn" @click="$router.push('/location')">Change location</button>
      </div>
    </template>

    <!-- zero results -->
    <template v-else-if="store.results.length === 0">
      <div class="empty-state">
        <span class="empty-glyph">?</span>
        <p class="empty-title">Nothing within {{ store.radiusKm }} km</p>
        <p class="empty-text">
          {{ store.message || `We couldn't find activity places within ${store.radiusKm} km of ${store.locationLabel}.` }}
          <template v-if="store.radiusKm < 10">Try a wider search radius.</template>
        </p>
        <button v-if="store.radiusKm < 10" class="btn btn-primary widen-btn" @click="widen">
          Search {{ nextRadius }} km instead
        </button>
      </div>
    </template>

    <!-- results: map with a pin per place, then one card per place -->
    <template v-else>
      <PlaceMap
        class="results-map"
        :center="store.coords"
        :places="store.results"
        fit
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
        <p v-if="justAdjusted" class="updated-tag">Updated to fit new window</p>

        <!-- Mission preview block. Mock until the missions endpoint is wired (see MOCK_MISSIONS). -->
        <div class="mission-block">
          <span class="badge mission">{{ missionFor(place).steps }}-task mission</span>
          <p class="mission-blurb"><b>"{{ missionFor(place).title }}"</b> — {{ missionFor(place).blurb }}</p>
        </div>
        <p class="duration-line">◷ {{ place.durationBucket }} min on-site · {{ place.comboTitle }}</p>
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

      <p class="section-label" style="margin-top: 16px">Maximum distance</p>
      <div class="seg-row">
        <button v-for="km in [3, 5, 10]" :key="km" class="seg-btn" :class="{ on: draft.radiusKm === km }" @click="draft.radiusKm = km">{{ km }} km</button>
      </div>

      <p class="section-label" style="margin-top: 18px">How long have you got</p>
      <button
        v-for="opt in DURATIONS"
        :key="opt.min"
        class="dur-row"
        :class="{ on: draft.durationMin === opt.min }"
        @click="draft.durationMin = opt.min"
      >
        <span>{{ opt.min }} min</span>
        <span class="dur-note">{{ opt.note }}</span>
      </button>

      <div class="btn-row" style="margin-top: 18px">
        <button class="btn btn-secondary" @click="adjusting = false">Cancel</button>
        <button class="btn btn-primary" @click="applyAdjust">Apply</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Top options for the current window (place + radius + duration). Reads
// store.results from POST /recommendations. Handles loading, error,
// out-of-pilot-area and zero-result states. The Adjust sheet changes radius
// and duration in place and refetches; location changes still go through the
// setup form via the crumb.

import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CategoryIcon from '../components/CategoryIcon.vue'
import ConditionBadge from '../components/ConditionBadge.vue'
import PlaceMap from '../components/PlaceMap.vue'
import { useSearchStore } from '../store'

const store = useSearchStore()
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

// Gap 2 — adjust distance and duration in place. Location is left alone; that
// still goes through the setup form. The three durations line up with the
// plan buckets the backend serves.
const DURATIONS = [
  { min: 20, note: 'a quick loop' },
  { min: 40, note: 'room for a full mission' },
  { min: 60, note: 'a proper outing' }
]
const adjusting = ref(false)
const justAdjusted = ref(false)
const draft = reactive({ radiusKm: store.radiusKm, durationMin: store.planMin })

function openAdjust() {
  draft.radiusKm = store.radiusKm
  draft.durationMin = store.planMin
  adjusting.value = true
}

function applyAdjust() {
  const changed = draft.radiusKm !== store.radiusKm || draft.durationMin !== store.planMin
  store.radiusKm = draft.radiusKm
  store.durationMin = draft.durationMin
  adjusting.value = false
  if (!changed) return
  justAdjusted.value = true
  store.fetchRecommendations()
}

function widen() {
  store.radiusKm = nextRadius.value
  store.fetchRecommendations()
}

function open(place) {
  router.push(`/place/${place.id}`)
}

function openById(id) {
  router.push(`/place/${id}`)
}
</script>

<style scoped>
.head-row { margin-top: 14px; }

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
  margin-top: 10px;
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

.dur-row {
  width: 100%;
  margin-top: 8px;
  height: 54px;
  padding: 0 16px;
  border: none;
  border-radius: var(--radius-field);
  background: var(--card);
  box-shadow: var(--shadow-card);
  color: var(--ink);
  font-size: 15.5px;
  font-weight: 600;
  font-family: inherit;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.18s ease;
}

.dur-row .dur-note { font-size: 13px; font-weight: 500; color: var(--ink-3); }
.dur-row.on { background: var(--green); color: var(--paper); box-shadow: var(--shadow-selected); }
.dur-row.on .dur-note { color: rgba(242, 241, 236, 0.75); }

.results-map { margin-top: 16px; }

.result-card {
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
.place-name.unnamed { color: var(--ink-3); font-style: italic; }
.place-meta { font-size: 13px; color: var(--ink-3); margin-top: 2px; }

.mission-block {
  margin-top: 12px;
  background: var(--paper);
  border-radius: 13px;
  padding: 11px 13px 12px;
}

.mission-blurb { font-size: 13.5px; line-height: 1.45; color: var(--ink-2); margin-top: 8px; }
.mission-blurb b { color: var(--ink); font-weight: 700; }
.duration-line { margin-top: 10px; font-size: 12px; color: var(--ink-4); }

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
