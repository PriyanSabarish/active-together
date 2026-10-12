<template>
  <template v-if="place">
    <!-- No app header on this page: the map is the top of the screen. -->
    <div class="scroll-area detail">
      <!-- Map hero: the same Leaflet map as the Play list, with back and temperature over it. -->
      <div class="hero">
        <div class="hero-map"><PlaceMap :center="placeCenter" :places="[place]" :pill="mapPill" :zoom="15" :show-you="false" height="100%" /></div>
        <div class="hero-fade" />
        <div class="hero-bar">
          <button class="round-btn" aria-label="All places" @click="$router.push('/play')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
          </button>
          <span class="temp-pill"><svg class="sun" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFD08A" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2" fill="#FFD08A" stroke="none" /><path d="M12 2.5v2.4 M12 19.1v2.4 M2.5 12h2.4 M19.1 12h2.4 M5.3 5.3l1.7 1.7 M17 17l1.7 1.7 M5.3 18.7 7 17 M17 7l1.7-1.7" /></svg>{{ facts.temp }}</span>
        </div>
      </div>

      <div class="sheet-body">
        <div class="title-block">
          <p class="eyebrow">{{ place.categoryLabel }} · {{ place.distanceKm }} km away</p>
          <h1 class="place-title">{{ place.name }}</h1>
        </div>

        <!-- Weather, UV and air quality from the current /data/context reading, then the trip there. -->
        <div class="facts-block">
          <div class="facts">
            <div class="fact fact-main">
              <svg class="sun" width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="#E8913A" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2" fill="#E8913A" stroke="none" /><path d="M12 2.5v2.4 M12 19.1v2.4 M2.5 12h2.4 M19.1 12h2.4 M5.3 5.3l1.7 1.7 M17 17l1.7 1.7 M5.3 18.7 7 17 M17 7l1.7-1.7" /></svg>
              <div class="fact-text">
                <p class="fact-big">{{ facts.temp }}</p>
                <p class="fact-note">{{ facts.rain }}</p>
              </div>
            </div>
            <div class="fact">
              <p class="fact-val">{{ facts.uv }} <span class="fact-tag">{{ facts.uvNote }}</span></p>
              <p class="fact-label">UV index</p>
            </div>
            <div class="fact">
              <p class="fact-val">{{ facts.air }}</p>
              <p class="fact-label">Air quality</p>
            </div>
          </div>

          <div class="walk-row">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="walk-icon"><path v-if="facts.driving" d="M5 16.5h14v-4.2l-1.8-4.3H6.8L5 12.3v4.2Z M5 12.5h14 M7.5 16.5v2 M16.5 16.5v2" /><template v-else><circle cx="13" cy="4.5" r="1.8" /><path d="M10 21l2.5-6 2.5 2.5V21 M12.5 15l-1-5.5 3.5 2 2 2.5 M11.5 9.5 8 11.5 7 15" /></template></svg>
            <p class="walk-text">
              {{ facts.travel }} {{ facts.mode }}
              <span class="walk-plan">· {{ place.durationBucket }} of your {{ place.enteredDurationMin }} min to play</span>
            </p>
            <button class="go-btn" @click="getDirections">Go ↗</button>
          </div>
        </div>

        <!-- Pick a mission: real POST /missions for this place, fetched on arrival.
             The parent reads them out, the child picks; the chosen mission's full
             task list is one tap away before anything starts (nothing hidden). -->
        <div class="missions">
          <div class="missions-head">
            <h2>Pick a mission</h2>
            <button class="shuffle" :disabled="missionStore.loading" @click="reloadMissions">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 14-5.3L20 9 M20 4v5h-5 M20 12a8 8 0 0 1-14 5.3L4 15 M4 20v-5h5" /></svg>
              Shuffle
            </button>
          </div>
          <p v-if="missionStore.noNewMissions" class="mission-status">That's every mission that fits this place right now.</p>
          <p v-if="missionStore.loading" class="mission-status">Finding missions…</p>
          <p v-else-if="missionStore.error" class="mission-status warn">{{ missionStore.error }} Showing what we can.</p>
          <p v-else-if="missionStore.candidates.length === 0" class="mission-status">No missions available for this place right now.</p>

          <div v-if="missionStore.candidates.length" class="cards">
            <article
              v-for="m in missionStore.candidates"
              :key="m.id"
              class="mcard"
              :class="{ on: chosenId === m.id }"
              role="button"
              tabindex="0"
              @click="chosenId = m.id"
              @keydown.enter="chosenId = m.id"
            >
              <div class="mcard-top">
                <span class="mcard-mins">{{ m.durationMin }} min</span>
                <span class="mcard-check">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5 10 17 19 7" /></svg>
                </span>
              </div>
              <p class="mcard-name">{{ m.title }}</p>
              <p v-if="m.equipment" class="mcard-eq">{{ m.equipment }}</p>
            </article>
          </div>

          <div v-if="chosen" class="steps-card">
            <button class="steps-head" :aria-expanded="stepsOpen" @click="stepsOpen = !stepsOpen">
              <span class="steps-title">{{ chosen.steps.length }} steps in {{ chosen.title.toLowerCase() }}</span>
              <span class="steps-chev" :class="{ up: stepsOpen }">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6" /></svg>
              </span>
            </button>
            <ol v-if="stepsOpen" class="steps">
              <li v-for="(step, i) in chosen.steps" :key="i">
                <span class="rail"><span class="dot" :class="{ first: i === 0 }" /><span v-if="i < chosen.steps.length - 1" class="line" /></span>
                <span class="step-text">{{ step.title }}</span>
              </li>
            </ol>
          </div>

          <div class="start-wrap">
            <button class="start" :disabled="!chosen" @click="startChosen">
              <span>{{ chosen ? `Start ${chosen.title.toLowerCase()}` : missionStore.loading ? 'Finding missions…' : 'No mission to start' }}</span>
              <span class="start-arrow">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14 M13 6l6 6-6 6" /></svg>
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
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
// One place in full: a map hero, weather / UV / air quality, the trip there,
// then the missions for this place from POST /missions, picked and
// started right here. Facts come from the same /data/context payload Start
// uses; the walking estimate is a pace over straight-line distance.
// Directions hand off to Google Maps.

import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import PlaceMap from '../components/PlaceMap.vue'
import { useSearchStore } from '../store'
import { categoryIcon } from '../taskIcons'
import { useMissionStore } from '../missionStore'
import { usePreferencesStore } from '../preferencesStore'
import { useHistoryStore } from '../historyStore'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const store = useSearchStore()
const missionStore = useMissionStore()
const preferencesStore = usePreferencesStore()
const historyStore = useHistoryStore()
const place = computed(() => store.place(props.id))

// The hero map is centred on the place, drawn as a pill with its category icon and distance.
const placeCenter = computed(() => (place.value ? { latitude: place.value.latitude, longitude: place.value.longitude } : null))
const mapPill = computed(() => (place.value ? { label: `${place.value.distanceKm} km`, icon: categoryIcon(place.value.category) } : null))

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
const stepsOpen = ref(false)
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
  stepsOpen.value = false
  missionStore.reloadMissions(place.value, {
    ageBand: preferencesStore.ageBand,
    preferences: preferencesStore.excludedCategories,
    recentTemplateIds: historyStore.recentTemplateIds(10)
  })
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

// The four fact tiles read the same context call the Start page uses; the
// travel estimate is the chosen mode's pace over the straight-line distance
// (walking ~5 km/h, driving ~30 km/h, the speeds Start uses for the radius).
const facts = computed(() => {
  const w = store.weather
  const ok = w && w.available !== false
  const rain = ok && w.precip_prob != null ? Math.round(w.precip_prob * 100) : null
  const [air, airNote] = airLabel(ok ? w.pm25 : null)
  const km = Number(place.value?.distanceKm ?? 0)
  // The mode is the one chosen on Start. The server's travel time is used when it
  // was worked out for that mode; otherwise the same straight-line estimate the
  // server falls back to (x1.3 over the straight line; walking 5 km/h, driving
  // 30 km/h plus 5 minutes to park).
  const driving = store.travelMode === 'driving'
  const tv = place.value?.travel?.mode === store.travelMode ? place.value.travel : null
  const estimateMin = km ? Math.max(1, Math.ceil(((km * 1.3) / (driving ? 30 : 5)) * 60 + (driving ? 5 : 0))) : null
  return {
    temp: ok && w.temp_c != null ? `${Math.round(w.temp_c)}°` : '—',
    rain: rain == null ? (ok ? 'No rain data' : 'Weather unavailable') : rain >= 50 ? 'Rain likely' : rain >= 25 ? `${rain}% rain` : 'Clear',
    uv: ok && w.uv_index != null ? String(w.uv_index) : '—',
    uvNote: uvNote(ok ? w.uv_index : null),
    air,
    airNote,
    // The server's travel block when the combo has one; the pace estimate only
    // for results that arrive without it.
    travel: tv ? `${tv.outMin} min` : estimateMin ? `${estimateMin} min` : '—',
    travelNote: tv
      ? `out, ${tv.source === 'openrouteservice' && tv.mode !== 'driving' ? 'routed' : 'estimated'}`
      : driving ? 'each way, by car' : 'each way, on foot',
    mode: driving ? 'drive' : 'walk',
    driving
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
.detail { padding-bottom: 0; margin-top: -24px; } /* map bleeds to the top edge, past the phone padding */

/* hero: edge to edge, the Play list's map style, with back and temperature over it */
.hero { position: relative; margin: 0 -24px; height: 260px; overflow: hidden; background: #E6E5DD; }
.hero-map { position: absolute; inset: 0; isolation: isolate; pointer-events: none; }
.hero-fade { position: absolute; inset: 0; z-index: 1; pointer-events: none; background: linear-gradient(180deg, rgba(242, 241, 236, 0.5) 0%, rgba(242, 241, 236, 0) 28%, rgba(242, 241, 236, 0) 80%, rgba(242, 241, 236, 0.5) 100%); }
.hero-bar { position: absolute; z-index: 3; top: calc(14px + env(safe-area-inset-top, 0px)); left: 16px; right: 16px; display: flex; justify-content: space-between; align-items: center; }
.round-btn, .temp-pill {
  height: 42px;
  border: none;
  border-radius: 999px;
  background: rgba(30, 42, 31, 0.55);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.round-btn { width: 42px; padding: 0; }
.temp-pill { padding: 0 14px; gap: 7px; font-size: 14px; font-weight: 700; color: #FFD08A; cursor: default; }

.sheet-body {
  position: relative;
  z-index: 4;
  margin: -26px -24px 0;
  padding: 20px 24px 0;
  border-radius: 28px 28px 0 0;
  background: var(--paper);
  box-shadow: 0 -10px 24px -14px rgba(30, 42, 31, 0.35);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.eyebrow { font-size: 12px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--green); }
.place-title { margin: 4px 0 0; font-size: 32px; line-height: 1.02; letter-spacing: -0.8px; }

.facts-block { display: flex; flex-direction: column; gap: 8px; }
.facts { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) minmax(0, 1fr); gap: 7px; }
.fact { border-radius: 19px; padding: 13px 12px; background: #FFFFFF; display: flex; flex-direction: column; justify-content: center; gap: 4px; min-width: 0; }
.fact-main { flex-direction: row; align-items: center; gap: 9px; }
.sun { flex: none; }
.fact-text { min-width: 0; }
.fact-big { font-family: var(--font-display); font-size: 23px; font-weight: 700; line-height: 1; letter-spacing: -0.5px; color: var(--ink); }
.fact-main .fact-note { margin-top: 3px; font-size: 12px; font-weight: 600; line-height: 1.2; color: #6B756D; overflow-wrap: anywhere; }
.fact-val { font-size: 18px; line-height: 1; font-weight: 700; color: var(--ink); }
.fact-tag { font-size: 12px; font-weight: 600; color: var(--green); }
.fact-label { font-size: 12px; font-weight: 600; color: #6B756D; }

.walk-row { border-radius: 22px; padding: 6px 6px 6px 12px; background: #DCE8F1; color: #2B5F82; display: flex; align-items: center; gap: 12px; }
.walk-icon { flex: none; }
.walk-text { flex: 1; min-width: 0; font-size: 13.5px; font-weight: 700; color: #1B3347; }
.walk-plan { font-weight: 500; color: #3F5F78; }
.go-btn { flex: none; height: 32px; padding: 0 12px; border: none; border-radius: 999px; background: #2B5F82; font-family: inherit; font-size: 12.5px; font-weight: 700; color: #FFFFFF; cursor: pointer; }

.missions { display: flex; flex-direction: column; gap: 12px; }
.missions-head { display: flex; align-items: center; justify-content: space-between; }
.missions-head h2 { margin: 0; font-size: 22px; letter-spacing: -0.4px; }
.shuffle { height: 34px; padding: 0 12px; border: none; border-radius: 999px; display: flex; align-items: center; gap: 6px; background: #E3ECDF; color: var(--green); font-family: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; }
.shuffle:disabled { opacity: 0.5; }
.mission-status { font-size: 13.5px; color: var(--ink-3); }
.mission-status.warn { color: var(--amber); }

.cards { display: flex; align-items: stretch; gap: 10px; overflow-x: auto; scrollbar-width: none; margin: 0 -24px; padding: 2px 24px 4px; scroll-padding: 0 24px; scroll-snap-type: x mandatory; }
.cards::-webkit-scrollbar { display: none; }
.mcard { flex: none; width: 236px; scroll-snap-align: start; display: flex; flex-direction: column; gap: 8px; padding: 16px; box-sizing: border-box; border-radius: 24px; cursor: pointer; transition: all 0.2s ease; background: #FFFFFF; color: var(--ink); box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.06); }
.mcard.on { background: var(--green); color: var(--paper); box-shadow: 0 16px 28px -16px rgba(47, 107, 54, 0.8); }
.mcard-top { display: flex; justify-content: space-between; align-items: center; }
.mcard-mins { font-size: 12px; font-weight: 700; color: var(--green); }
.mcard.on .mcard-mins { color: #B4D278; }
.mcard-check { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: transparent; box-shadow: inset 0 0 0 1.5px rgba(30, 42, 31, 0.2); color: transparent; }
.mcard.on .mcard-check { background: #B4D278; box-shadow: none; color: #1E2A1F; }
.mcard-name { font-family: var(--font-display); font-size: 21px; font-weight: 700; letter-spacing: -0.4px; line-height: 1.1; }
.mcard-eq { font-size: 12.5px; line-height: 1.35; color: var(--ink-3); }
.mcard.on .mcard-eq { color: rgba(242, 241, 236, 0.75); }

.steps-card { border-radius: 22px; background: #FFFFFF; box-shadow: 0 0 0 1px rgba(30, 42, 31, 0.06); overflow: hidden; }
.steps-head { width: 100%; display: flex; align-items: center; gap: 10px; min-height: 56px; padding: 0 14px 0 16px; border: none; background: none; font-family: inherit; text-align: left; cursor: pointer; }
.steps-title { flex: 1; min-width: 0; font-size: 14px; font-weight: 700; color: var(--ink); }
.steps-chev { width: 30px; height: 30px; flex: none; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #E3ECDF; color: var(--green); transition: transform 0.2s ease; }
.steps-chev.up { transform: rotate(180deg); }
.steps { list-style: none; margin: 0; padding: 0 16px 8px; display: flex; flex-direction: column; }
.steps li { display: flex; gap: 12px; align-items: stretch; }
.rail { flex: none; width: 16px; display: flex; flex-direction: column; align-items: center; padding-top: 2px; }
.dot { flex: none; width: 14px; height: 14px; box-sizing: border-box; border-radius: 50%; border: 2px solid var(--green); background: #FFFFFF; }
.dot.first { background: var(--green); box-shadow: 0 0 0 3px rgba(47, 107, 54, 0.14); }
.line { flex: 1; width: 0; min-height: 8px; margin: 3px 0 1px; border-left: 2px dotted rgba(47, 107, 54, 0.35); }
.step-text { flex: 1; min-width: 0; padding: 1px 0 12px; font-size: 13.5px; font-weight: 500; line-height: 1.35; color: #3F4A41; }

.start-wrap { position: sticky; bottom: 0; z-index: 5; margin: 0 -24px; padding: 12px 24px; background: linear-gradient(180deg, rgba(242, 241, 236, 0) 0%, rgba(242, 241, 236, 0.85) 45%); }
.start { position: relative; width: 100%; display: flex; align-items: center; justify-content: space-between; height: 58px; padding: 0 9px 0 24px; border: none; border-radius: 999px; background: var(--green); color: var(--paper); font-family: inherit; font-size: 16.5px; font-weight: 700; cursor: pointer; box-shadow: 0 14px 28px -14px rgba(47, 107, 54, 0.75); }
.start:active { transform: scale(0.985); }
.start:disabled { opacity: 0.5; cursor: not-allowed; }
.start-arrow { width: 40px; height: 40px; flex: none; border-radius: 50%; background: var(--paper); display: flex; align-items: center; justify-content: center; }
</style>
