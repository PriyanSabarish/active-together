<template>
  <AppHeader back />
  <!-- Setup step 2: on-site minutes, matched plan bucket, and the live forecast. -->

  <div class="scroll-area">
    <h1>How long have you got?</h1>
    <p class="subtitle">We'll match this to travel time and the forecast for your starting point.</p>

    <div class="time-card">
      <div class="time-head">
        <span class="time-label">On-site time</span>
        <span class="time-value duration-value">{{ store.durationMin }} min</span>
      </div>
      <!-- --fill drives the coloured part of the track (see .duration in <style>). -->
      <input
        v-model.number="store.durationMin"
        type="range"
        min="20"
        max="120"
        step="5"
        class="duration"
        :style="{ '--fill': ((store.durationMin - 20) / 100) * 100 + '%' }"
      />
      <div class="ticks">
        <span v-for="t in [20, 40, 60, 80, 100, 120]" :key="t">{{ t }}</span>
      </div>
      <p class="time-note">Not including travel.</p>
    </div>

    <div class="plan-card">
      <span class="plan-icon">✓</span>
      <div>
        <p class="plan-title">Matched to a {{ store.planMin }}-minute plan</p>
        <p class="plan-note">Plans come in 20, 40 and 60 minutes. Ties at 30 or 50 min round to the lower plan.</p>
      </div>
    </div>

    <p class="section-label" style="margin-top: 22px">Right now near {{ store.locationLabel }}</p>
    <div class="weather-card">
      <template v-if="store.contextLoading">
        <span class="wx-spinner" />
        <div>
          <p class="weather-main">Checking the forecast…</p>
          <p class="weather-sub">Live data from Open-Meteo</p>
        </div>
      </template>

      <template v-else-if="!wx || !wx.available">
        <span class="wx-glyph muted">?</span>
        <div>
          <p class="weather-main">Weather unavailable</p>
          <p class="weather-sub">We'll still show places; conditions will be marked unavailable.</p>
        </div>
      </template>

      <template v-else>
        <span class="wx-glyph" :class="rainPct == null || rainPct < 25 ? 'sun' : 'rain'">
          <svg v-if="rainPct == null || rainPct < 25" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <circle cx="12" cy="12" r="5" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          </svg>
          <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 15a4 4 0 0 1 .6-7.95A6 6 0 0 1 19 9a3.5 3.5 0 0 1-1 6.86H7Z" /><path d="M9 18l-1 3M13 18l-1 3M17 18l-1 3" />
          </svg>
        </span>
        <div>
          <p class="weather-main">{{ weatherMain }}</p>
          <p class="weather-sub">{{ weatherSub }}</p>
        </div>
      </template>
    </div>
  </div>

  <button class="btn btn-primary cta" @click="findActivities">See what fits <span class="btn-arrow">→</span></button>
</template>

<script setup>
// Setup step 2 — how long have you got. On-site minutes (20-120) are mapped
// by the store to the backend's 20/40/60 plan buckets. Also shows the live
// forecast for the chosen point from /data/context. "See what fits" marks
// setup as done and fires the recommendations request.

import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useSearchStore } from '../store'

const store = useSearchStore()
const router = useRouter()

onMounted(() => {
  if (store.hasLocation) store.loadContext()
})

const wx = computed(() => store.weather)

const rainPct = computed(() =>
  wx.value?.precip_prob == null ? null : Math.round(wx.value.precip_prob * 100)
)

// Headline: temperature and rain chance, whichever readings exist.
const weatherMain = computed(() => {
  const parts = []
  if (wx.value?.temp_c != null) parts.push(`${Math.round(wx.value.temp_c)}°C`)
  if (rainPct.value != null) parts.push(`${rainPct.value}% chance of rain`)
  return parts.length ? parts.join(', ') : 'Conditions available'
})

// Secondary line: UV, gusts and PM2.5, again only what the backend returned.
const weatherSub = computed(() => {
  const parts = []
  if (wx.value?.uv_index != null) parts.push(`UV ${wx.value.uv_index}`)
  if (wx.value?.wind_gust_kmh != null) parts.push(`gusts ${Math.round(wx.value.wind_gust_kmh)} km/h`)
  if (wx.value?.pm25 != null) parts.push(`PM2.5 ${Math.round(wx.value.pm25)}`)
  return parts.length ? parts.join(' · ') : 'Some readings are missing for this time'
})

function findActivities() {
  store.setupDone = true
  store.fetchRecommendations()
  router.push('/results')
}
</script>

<style scoped>
.time-card {
  margin-top: 18px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 16px 18px 14px;
}

.time-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 14px; }
.time-label { font-size: 13.5px; font-weight: 600; color: var(--ink-3); }
.time-value { font-family: var(--font-display); font-size: 24px; font-weight: 600; letter-spacing: -0.5px; }

.duration {
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(
    to right,
    var(--green) 0%,
    var(--green) var(--fill, 25%),
    var(--line-2) var(--fill, 25%),
    var(--line-2) 100%
  );
  outline: none;
}

.duration::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--card);
  border: 3px solid var(--green);
  box-shadow: var(--shadow-card);
  cursor: pointer;
}

.duration::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--card);
  border: 3px solid var(--green);
  cursor: pointer;
}

.ticks {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 10px;
  color: var(--ink-5);
}

.time-note { font-size: 12.5px; color: var(--ink-4); margin-top: 10px; }

.plan-card {
  margin-top: 12px;
  border-radius: var(--radius-field);
  background: var(--green-light);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.plan-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--green);
  color: var(--paper);
  font-size: 13px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.plan-title { font-size: 14px; font-weight: 600; color: var(--green-dark); }
.plan-note { font-size: 12px; color: var(--green); margin-top: 3px; line-height: 1.4; }

.weather-card {
  border-radius: var(--radius-card);
  background: var(--card);
  box-shadow: var(--shadow-card);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.wx-glyph {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 700;
}

.wx-glyph.sun { background: var(--amber-light); color: var(--accent); }
.wx-glyph.rain { background: var(--tint); color: var(--ink-3); }
.wx-glyph.muted { background: var(--tint); color: var(--ink-4); }

.wx-spinner {
  width: 26px;
  height: 26px;
  margin: 7px;
  border: 2.5px solid var(--green);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.weather-main { font-size: 15.5px; font-weight: 600; }
.weather-sub { font-size: 12.5px; color: var(--ink-3); margin-top: 3px; }

.cta { width: 100%; margin-top: 14px; }
</style>
