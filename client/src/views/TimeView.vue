<template>
  <AppHeader :step="2" back />

  <div class="scroll-area">
  <h1>How long do you have</h1>
  <p class="subtitle">Recommendations use the current forecast for your starting point.</p>

  <p class="section-label" style="margin-top: 18px">On-site time (not including travel)</p>
  <div class="slider-wrap">
    <input
      v-model.number="store.durationMin"
      type="range"
      min="20"
      max="120"
      step="5"
      class="duration"
      :style="{ '--fill': ((store.durationMin - 20) / 100) * 100 + '%' }"
    />
    <span class="duration-value">{{ store.durationMin }} min</span>
  </div>
  <div class="ticks">
    <span v-for="t in [20, 40, 60, 80, 100, 120]" :key="t">{{ t }}</span>
  </div>

  <div class="plan-card">
    <svg width="18" height="18" viewBox="0 0 18 18">
      <circle cx="9" cy="9" r="8" fill="none" stroke="#27500A" stroke-width="1.5" />
      <line x1="9" y1="5" x2="9" y2="9.5" stroke="#27500A" stroke-width="1.5" />
      <circle cx="9" cy="12.5" r="0.9" fill="#27500A" />
    </svg>
    <div>
      <p class="plan-title">Matched to a {{ store.planMin }}-minute plan</p>
      <p class="plan-note">Plans come in 20, 40 and 60 minutes. Ties at 30 or 50 min round to the lower plan.</p>
    </div>
  </div>

  <hr class="divider" />

  <p class="section-label">Right now near {{ store.locationLabel }}</p>
  <div class="weather-card">
    <template v-if="store.contextLoading">
      <span class="wx-spinner" />
      <div>
        <p class="weather-main">Checking the forecast…</p>
        <p class="weather-sub">Live data from Open-Meteo</p>
      </div>
    </template>

    <template v-else-if="!wx || !wx.available">
      <svg width="44" height="44" viewBox="0 0 44 44">
        <circle cx="22" cy="22" r="17" fill="none" stroke="#B4B2A9" stroke-width="2.5" />
        <path d="M16 17 a6 6 0 1 1 8.5 5.5 c-2 1 -2.5 2.2 -2.5 4" fill="none" stroke="#B4B2A9" stroke-width="2.5" stroke-linecap="round" />
        <circle cx="22" cy="31.5" r="1.8" fill="#B4B2A9" />
      </svg>
      <div>
        <p class="weather-main">Weather unavailable</p>
        <p class="weather-sub">We'll still show places; conditions will be marked unavailable.</p>
      </div>
    </template>

    <template v-else>
      <svg v-if="rainPct == null || rainPct < 25" width="44" height="44" viewBox="0 0 44 44">
        <circle cx="22" cy="22" r="12" fill="none" stroke="#BA7517" stroke-width="2.5" />
        <line x1="22" y1="3" x2="22" y2="7" stroke="#BA7517" stroke-width="2" />
        <line x1="22" y1="37" x2="22" y2="41" stroke="#BA7517" stroke-width="2" />
        <line x1="3" y1="22" x2="7" y2="22" stroke="#BA7517" stroke-width="2" />
        <line x1="37" y1="22" x2="41" y2="22" stroke="#BA7517" stroke-width="2" />
      </svg>
      <svg v-else width="44" height="44" viewBox="0 0 44 44">
        <path d="M12 26 a8 8 0 1 1 2 -15 a10 10 0 0 1 19 3 a7 7 0 0 1 -2 12 Z" fill="none" stroke="#5F5E5A" stroke-width="2.5" stroke-linejoin="round" />
        <line x1="16" y1="32" x2="14" y2="38" stroke="#5F5E5A" stroke-width="2" stroke-linecap="round" />
        <line x1="24" y1="32" x2="22" y2="38" stroke="#5F5E5A" stroke-width="2" stroke-linecap="round" />
        <line x1="32" y1="32" x2="30" y2="38" stroke="#5F5E5A" stroke-width="2" stroke-linecap="round" />
      </svg>
      <div>
        <p class="weather-main">{{ weatherMain }}</p>
        <p class="weather-sub">{{ weatherSub }}</p>
      </div>
    </template>
  </div>
  </div>

  <div class="btn-row">
    <button class="btn btn-secondary" @click="$router.back()">Back</button>
    <button class="btn btn-primary" @click="findActivities">Find activities</button>
  </div>
</template>

<script setup>
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

const weatherMain = computed(() => {
  const parts = []
  if (wx.value?.temp_c != null) parts.push(`${Math.round(wx.value.temp_c)}°C`)
  if (rainPct.value != null) parts.push(`${rainPct.value}% chance of rain`)
  return parts.length ? parts.join(', ') : 'Conditions available'
})

const weatherSub = computed(() => {
  const parts = []
  if (wx.value?.uv_index != null) parts.push(`UV ${wx.value.uv_index}`)
  if (wx.value?.wind_gust_kmh != null) parts.push(`gusts ${Math.round(wx.value.wind_gust_kmh)} km/h`)
  if (wx.value?.pm25 != null) parts.push(`PM2.5 ${Math.round(wx.value.pm25)}`)
  return parts.length ? parts.join(' · ') : 'Some readings are missing for this time'
})

function findActivities() {
  store.fetchRecommendations()
  router.push('/results')
}
</script>

<style scoped>
.mode-row {
  display: flex;
  gap: 8px;
  margin: 18px 0 12px;
}

.mode-btn {
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

.mode-btn.on {
  background: var(--green);
  border-color: var(--green);
  color: var(--green-light);
  font-weight: 500;
}

.select-field {
  height: 46px;
  border: 1px solid var(--line-3);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 15px;
  margin-bottom: 8px;
  position: relative;
}

.select-field select {
  appearance: none;
  -webkit-appearance: none;
  border: none;
  outline: none;
  background: transparent;
  flex: 1;
  font-size: 13.5px;
  font-family: inherit;
  color: var(--ink);
  cursor: pointer;
}

.select-field .chev { pointer-events: none; }

.slider-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
}

.duration {
  flex: 1;
  appearance: none;
  -webkit-appearance: none;
  height: 4px;
  border-radius: 2px;
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
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 2.5px solid var(--green);
  cursor: pointer;
}

.duration::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 2.5px solid var(--green);
  cursor: pointer;
}

.duration-value {
  font-size: 14px;
  font-weight: 500;
  width: 56px;
  text-align: right;
}

.ticks {
  display: flex;
  justify-content: space-between;
  margin: 8px 72px 0 0;
  font-size: 9px;
  color: var(--ink-5);
}

.plan-card {
  margin-top: 16px;
  border-radius: 10px;
  background: var(--green-light);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.plan-title {
  font-size: 12.5px;
  font-weight: 500;
  color: var(--green-dark);
}

.plan-note {
  font-size: 10.5px;
  color: var(--green);
  margin-top: 3px;
}

.weather-card {
  border-radius: 12px;
  background: var(--paper);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 18px;
}

.wx-spinner {
  width: 26px;
  height: 26px;
  margin: 9px;
  border: 2.5px solid var(--green-dark);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.weather-main { font-size: 14.5px; font-weight: 500; }
.weather-sub { font-size: 11px; color: var(--ink-3); margin-top: 4px; }
</style>
