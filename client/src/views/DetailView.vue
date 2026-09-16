<template>
  <template v-if="place">
    <AppHeader />

    <div class="scroll-area">
      <button class="pill crumb" @click="$router.back()">‹ All places</button>

      <h1 class="place-title">{{ place.name }}</h1>
      <p class="subtitle">
        {{ place.categoryLabel }} · {{ place.distanceKm }} km away
        <span v-if="place.recordId" class="record-id">#{{ place.recordId }}</span>
      </p>

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

      <PlaceMap class="map-card" :center="store.coords" :places="[place]" fit height="130px" />

      <h2 class="sect">Why this place</h2>
      <p class="sect-sub explanation">{{ place.reason }}</p>
      <ul class="info-card why-list">
        <li v-for="r in place.reasons" :key="r" class="info-row">{{ r }}</li>
      </ul>

      <h2 class="sect">Conditions when you go</h2>
      <div class="info-card">
        <p v-for="c in place.conditions" :key="c.text" class="info-row cond condition-row" :class="c.icon">
          <span class="cond-dot" />{{ c.text }}
        </p>
      </div>

      <h2 class="sect">What to expect</h2>
      <div class="info-card">
        <p class="info-title">{{ place.comboTitle }}</p>
        <p class="info-body expect">{{ place.expect }}</p>
      </div>

      <p class="disclaimer">Candidate activity opportunity — opening hours, cost and accessibility aren't available yet.</p>
    </div>

    <div class="btn-row" style="margin-top: 14px">
      <button class="btn btn-secondary" @click="getDirections">Directions</button>
      <button class="btn btn-primary" @click="$router.push('/play/pick')">Pick a mission <span class="btn-arrow">→</span></button>
    </div>
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area">
      <button class="pill crumb" @click="$router.push('/results')">‹ All places</button>
      <p class="subtitle" style="margin-top: 20px">
        {{ store.loading ? 'Loading your top options…' : 'Place not found.' }}
      </p>
    </div>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import ConditionBadge from '../components/ConditionBadge.vue'
import PlaceMap from '../components/PlaceMap.vue'
import { useSearchStore } from '../store'

const props = defineProps({ id: { type: String, required: true } })
const store = useSearchStore()
const place = computed(() => store.place(props.id))

// Landing here directly (e.g. page refresh) — the inputs are restored from
// storage but results are not, so run the search again and let `place` resolve.
if (!place.value && !store.loading && store.status === 'idle') store.fetchRecommendations()

function uvNote(uv) {
  if (uv == null) return 'No reading'
  if (uv < 3) return 'Low'
  if (uv < 6) return 'Moderate'
  if (uv < 8) return 'High'
  return 'Very high'
}

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
.why-list { list-style: none; }

.map-card { margin-top: 14px; }

.sect { margin-top: 22px; }
.sect-sub { font-size: 13.5px; color: var(--ink-3); line-height: 1.45; margin-top: 3px; }

.info-card {
  margin-top: 10px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 6px 16px;
}

.info-row {
  font-size: 13.5px;
  color: var(--ink-2);
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-row:last-child { border-bottom: none; }

.cond-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); flex-shrink: 0; }
.cond.wind .cond-dot { background: var(--accent); }
.cond.unknown .cond-dot { background: var(--ink-5); }

.info-title { font-size: 15px; font-weight: 600; padding-top: 10px; }
.info-body { font-size: 13.5px; color: var(--ink-2); line-height: 1.5; padding: 4px 0 10px; }

.disclaimer {
  margin-top: 16px;
  font-size: 12px;
  color: var(--ink-4);
  line-height: 1.45;
}
</style>
