<template>
  <template v-if="place">
    <AppHeader />

    <div class="scroll-area">
      <button class="pill crumb" @click="$router.push('/play')">‹ All places</button>

      <h1 class="place-title">{{ place.name }}</h1>
      <p class="subtitle">
        {{ place.categoryLabel }} · {{ place.distanceKm }} km away
        <span v-if="place.recordId" class="record-id">#{{ place.recordId }}</span>
      </p>

      <!-- Four fact tiles, all from the current /data/context reading plus distance. -->
      <div class="fact-grid">
        <div class="fact-tile">
          <p class="fact-label">☂ Weather</p>
          <p class="fact-value">{{ facts.temp }}</p>
          <p class="fact-note">{{ facts.rain }}</p>
        </div>
        <div class="fact-tile">
          <p class="fact-label">☀ UV</p>
          <p class="fact-value">{{ facts.uv }}</p>
          <p class="fact-note">{{ facts.uvNote }}</p>
        </div>
        <div class="fact-tile">
          <p class="fact-label">≋ Air quality</p>
          <p class="fact-value">{{ facts.air }}</p>
          <p class="fact-note">{{ facts.airNote }}</p>
        </div>
        <div class="fact-tile">
          <p class="fact-label">◷ Travel time</p>
          <p class="fact-value">{{ facts.travel }}</p>
          <p class="fact-note">each way, on foot</p>
        </div>
      </div>

      <div class="plan-line">
        <ConditionBadge :badge="place.badge" />
        <span>
          <span class="duration-main">{{ place.durationBucket }}-minute on-site plan</span>
          <span class="duration-sub">Matches your {{ place.enteredDurationMin }}-min request · excludes travel</span>
        </span>
      </div>


      <p class="disclaimer" style="margin-top: 14px"><button class="link-btn" @click="getDirections">Directions ↗</button></p>

      <!-- Pick a mission: real POST /missions for this place, fetched on arrival.
           The parent reads them out, the child picks; every card can show its
           full task list before anything starts (nothing hidden). -->
      <h2 class="sect">Pick a mission</h2>
      <p class="sect-sub">Read these out. Daniel picks — the phone stays with you.</p>

      <button class="link-btn reload-btn" :disabled="missionStore.loading" @click="reloadMissions">
        ↻ Show different missions
      </button>
      <p v-if="missionStore.noNewMissions" class="mission-status">That's every mission that fits this place right now.</p>

      <p v-if="missionStore.loading" class="mission-status">Finding missions…</p>
      <p v-else-if="missionStore.error" class="mission-status warn">{{ missionStore.error }} Showing what we can.</p>
      <p v-else-if="missionStore.candidates.length === 0" class="mission-status">No missions available for this place right now.</p>

      <article
        v-for="m in missionStore.candidates"
        :key="m.id"
        class="mission-card"
        :class="{ on: chosenId === m.id }"
        role="button"
        tabindex="0"
        @click="chosenId = m.id"
        @keydown.enter="chosenId = m.id"
      >
        <div class="mission-top">
          <span class="mission-title">{{ m.title }}</span>
          <span class="mission-meta">{{ m.steps.length }} tasks · {{ m.durationMin }} min</span>
        </div>
        <p class="mission-line">{{ m.equipment }}</p>
        <button class="tasks-toggle" @click.stop="toggleTasks(m.id)">
          {{ openId === m.id ? 'Hide tasks ▴' : 'See tasks ▾' }}
        </button>
        <ul v-if="openId === m.id" class="task-list">
          <li v-for="(step, i) in m.steps" :key="i">
            <span class="task-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path :d="taskIcon(step.icon)" /></svg></span>
            {{ step.title }}
          </li>
        </ul>
      </article>
    </div>

    <button class="btn btn-primary cta" :disabled="!chosen" @click="startChosen">
      {{ chosen ? `Start ${chosen.title.toLowerCase()}` : missionStore.loading ? 'Finding missions…' : 'No mission to start' }}
    </button>
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area">
      <button class="pill crumb" @click="$router.push('/play')">‹ All places</button>
      <p class="subtitle" style="margin-top: 20px">
        {{ store.loading ? 'Loading your top options…' : 'Place not found.' }}
      </p>
    </div>
  </template>
</template>

<script setup>
// One place in full: four fact tiles (weather, UV, air, walking time), why it
// appears, then the missions for this place from POST /missions, picked and
// started right here. Facts come from the same /data/context payload Start
// uses; the walking estimate is a pace over straight-line distance.
// Directions hand off to Google Maps.

import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import ConditionBadge from '../components/ConditionBadge.vue'
import { useSearchStore } from '../store'
import { useMissionStore } from '../missionStore'
import { usePreferencesStore } from '../preferencesStore'
import { useHistoryStore } from '../historyStore'
import { taskIcon } from '../taskIcons'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const store = useSearchStore()
const missionStore = useMissionStore()
const preferencesStore = usePreferencesStore()
const historyStore = useHistoryStore()
const place = computed(() => store.place(props.id))

// Real POST /missions for this specific place, using the plan already agreed
// here (place.durationBucket), the parent's age band and category
// preferences, and recent history so B33's "not twice in a row" has
// something to exclude. Fetched as soon as the place resolves, so the list
// below is never a stale set from a previous place.
watch(
  place,
  (p) => {
    if (!p) return
    missionStore.fetchMissions(p, {
      ageBand: preferencesStore.ageBand,
      preferences: preferencesStore.excludedCategories,
      recentTemplateIds: historyStore.recentTemplateIds(10)
    })
  },
  { immediate: true }
)

// Mission pick. The first candidate is pre-selected once they arrive so
// "Start" always has a target.
const chosenId = ref(null)
const openId = ref(null)
watch(
  () => missionStore.candidates,
  (list) => {
    if (!list.some((m) => m.id === chosenId.value)) chosenId.value = list[0]?.id ?? null
  },
  { immediate: true }
)
const chosen = computed(() => missionStore.candidates.find((m) => m.id === chosenId.value) ?? null)

function reloadMissions() {
  if (!place.value) return
  openId.value = null
  missionStore.reloadMissions(place.value, {
    ageBand: preferencesStore.ageBand,
    preferences: preferencesStore.excludedCategories,
    recentTemplateIds: historyStore.recentTemplateIds(10)
  })
}

function toggleTasks(id) {
  openId.value = openId.value === id ? null : id
}

function startChosen() {
  if (!chosen.value) return
  missionStore.chooseMission(chosen.value.id)
  missionStore.startMission()
  router.push('/play/run')
}

// Landing here directly (e.g. page refresh) — the inputs are restored from
// storage but results are not, so run the search again and let `place` resolve.
if (!place.value && !store.loading && store.status === 'idle') store.fetchRecommendations()

// WHO UV index bands, used for the tile note.
function uvNote(uv) {
  if (uv == null) return 'No reading'
  if (uv < 3) return 'Low'
  if (uv < 6) return 'Moderate'
  if (uv < 8) return 'High'
  return 'Very high'
}

// Rough PM2.5 bands for a parent-facing label; not an official AQI.
function airLabel(pm) {
  if (pm == null) return ['—', 'No reading']
  if (pm <= 12) return ['Good', 'No warnings']
  if (pm <= 35) return ['Fair', 'Fine for most']
  return ['Poor', 'Keep it short']
}

// The four fact tiles read the same context call the Time screen uses; the
// travel estimate is a walking pace over the straight-line distance.
const facts = computed(() => {
  const w = store.weather
  const ok = w && w.available !== false
  const rain = ok && w.precip_prob != null ? Math.round(w.precip_prob * 100) : null
  const [air, airNote] = airLabel(ok ? w.pm25 : null)
  const km = Number(place.value?.distanceKm ?? 0)
  return {
    temp: ok && w.temp_c != null ? `${Math.round(w.temp_c)}°` : '—',
    rain: rain == null ? (ok ? 'No rain data' : 'Weather unavailable') : rain >= 50 ? 'Rain likely' : rain >= 25 ? `${rain}% chance of rain` : 'Clear',
    uv: ok && w.uv_index != null ? `UV ${w.uv_index}` : '—',
    uvNote: uvNote(ok ? w.uv_index : null),
    air,
    airNote,
    travel: km ? `${Math.max(1, Math.round(km * 12))} min` : '—'
  }
})

function getDirections() {
  // Hand off to Google Maps using the place coordinates from the backend so
  // unnamed places still resolve.
  const q = encodeURIComponent(`${place.value.latitude},${place.value.longitude}`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank')
}
</script>

<style scoped>
.place-title { margin-top: 14px; }

.link-btn { background: none; border: none; padding: 0; margin-left: 6px; color: var(--green); font-size: 12px; font-weight: 600; font-family: inherit; cursor: pointer; }

.sect-sub { font-size: 13.5px; color: var(--ink-3); line-height: 1.45; margin-top: 3px; }
.reload-btn { display: block; margin: 10px 0 0; font-size: 13px; }
.reload-btn:disabled { opacity: 0.5; }
.mission-status { margin-top: 10px; font-size: 13.5px; color: var(--ink-3); }
.mission-status.warn { color: var(--amber); }

.mission-card {
  margin-top: 10px;
  padding: 15px 18px 14px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all 0.18s ease;
}

.mission-card.on { background: var(--green); color: var(--paper); box-shadow: 0 10px 24px rgba(47, 107, 54, 0.24); }
.mission-top { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.mission-title { font-family: var(--font-display); font-size: 17.5px; font-weight: 600; letter-spacing: -0.2px; }
.mission-meta { font-size: 13px; font-weight: 600; color: var(--ink-4); white-space: nowrap; }
.mission-card.on .mission-meta { color: var(--accent); }
.mission-line { margin-top: 4px; font-size: 13.5px; line-height: 1.4; color: var(--ink-3); }
.mission-card.on .mission-line { color: rgba(242, 241, 236, 0.75); }

.tasks-toggle { margin-top: 12px; background: none; border: none; padding: 0; font-family: inherit; font-size: 13.5px; font-weight: 600; color: var(--green); cursor: pointer; }
.mission-card.on .tasks-toggle { color: var(--paper); }

.task-list { list-style: none; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--line); }
.mission-card.on .task-list { border-top-color: rgba(242, 241, 236, 0.2); }
.task-list li { display: flex; align-items: center; gap: 10px; padding: 6px 0; font-size: 13.5px; }
.task-icon { width: 26px; height: 26px; border-radius: 50%; background: var(--green-light); color: var(--green); display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mission-card.on .task-icon { background: rgba(242, 241, 236, 0.16); color: var(--paper); }

.cta { width: 100%; margin-top: 14px; }

.record-id {
  margin-left: 6px;
  font-size: 11px;
  color: var(--ink-5);
  font-variant-numeric: tabular-nums;
}

.fact-grid { margin-top: 16px; }

.plan-line {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 14px;
  font-size: 12.5px;
  color: var(--ink-3);
  line-height: 1.4;
}

.duration-main { display: block; font-weight: 600; color: var(--ink-2); }
.duration-sub { display: block; margin-top: 2px; }

.sect { margin-top: 22px; }


.mission-fetch-error {
  margin-top: 14px;
  font-size: 12.5px;
  color: var(--amber);
  line-height: 1.4;
}
</style>
