<template>
  <AppHeader :step="2" back />

  <h1>When are you free</h1>
  <p class="subtitle">Limited to today's forecast window.</p>

  <div class="mode-row">
    <button class="mode-btn" :class="{ on: store.timeMode === 'now' }" @click="store.timeMode = 'now'">Now</button>
    <button class="mode-btn" :class="{ on: store.timeMode === 'pick' }" @click="store.timeMode = 'pick'">Pick a time</button>
  </div>

  <template v-if="store.timeMode === 'pick'">
    <div class="select-field">
      <svg width="16" height="16" viewBox="0 0 17 17">
        <rect x="1" y="3" width="15" height="13" rx="2" fill="none" stroke="#5F5E5A" stroke-width="1.5" />
        <line x1="1" y1="7" x2="16" y2="7" stroke="#5F5E5A" stroke-width="1.5" />
        <line x1="5" y1="1" x2="5" y2="4" stroke="#5F5E5A" stroke-width="1.5" />
        <line x1="12" y1="1" x2="12" y2="4" stroke="#5F5E5A" stroke-width="1.5" />
      </svg>
      <select v-model="day">
        <option>Today</option>
      </select>
      <svg class="chev" width="12" height="8" viewBox="0 0 14 8"><path d="M1 1 l6 6 l6 -6" fill="none" stroke="#888780" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
    </div>

    <div class="select-field">
      <svg width="16" height="16" viewBox="0 0 17 17">
        <circle cx="8.5" cy="8.5" r="7.5" fill="none" stroke="#5F5E5A" stroke-width="1.5" />
        <line x1="8.5" y1="8.5" x2="8.5" y2="3.5" stroke="#5F5E5A" stroke-width="1.5" stroke-linecap="round" />
        <line x1="8.5" y1="8.5" x2="12.5" y2="10.5" stroke="#5F5E5A" stroke-width="1.5" stroke-linecap="round" />
      </svg>
      <select v-model.number="store.hour">
        <option v-for="f in FORECAST" :key="f.h" :value="f.h">{{ f.label }}</option>
      </select>
      <svg class="chev" width="12" height="8" viewBox="0 0 14 8"><path d="M1 1 l6 6 l6 -6" fill="none" stroke="#888780" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
    </div>
  </template>

  <hr class="divider" />

  <p class="section-label">On-site time (not including travel)</p>
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
      <p class="plan-note">Ties at 30 or 50 min round to the lower plan.</p>
    </div>
  </div>

  <hr class="divider" />

  <p class="section-label">{{ timeCaption }} near {{ store.locationLabel }}</p>
  <div class="weather-card">
    <svg v-if="wx.rain < 25" width="44" height="44" viewBox="0 0 44 44">
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
      <p class="weather-main">{{ wx.temp }}°C, {{ wx.desc }}</p>
      <p class="weather-sub">{{ rainLabel }} · UV {{ wx.uv }} · {{ windLabel }}</p>
    </div>
  </div>

  <div class="btn-row">
    <button class="btn btn-secondary" @click="$router.back()">Back</button>
    <button class="btn btn-primary" @click="findActivities">Find activities</button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useSearchStore, FORECAST } from '../store'

const store = useSearchStore()
const router = useRouter()
const day = ref('Today')

const wx = computed(() => store.weather)

const timeCaption = computed(() =>
  store.timeMode === 'now' ? 'Right now' : `At ${wx.value.label} today`
)

const rainLabel = computed(() => {
  if (wx.value.rain >= 50) return 'High rain chance'
  if (wx.value.rain >= 25) return 'Medium rain chance'
  return 'Low rain chance'
})

const windLabel = computed(() => {
  if (wx.value.wind >= 28) return 'strong wind'
  if (wx.value.wind >= 20) return 'fresh wind'
  return 'light wind'
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

.weather-main { font-size: 14.5px; font-weight: 500; }
.weather-sub { font-size: 11px; color: var(--ink-3); margin-top: 4px; }
</style>
