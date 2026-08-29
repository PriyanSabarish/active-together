<template>
  <template v-if="place">
    <div class="app-bar">
      <button class="back-btn" aria-label="Back to your top 3" @click="$router.back()">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <span class="crumb">Back to your top 3</span>
    </div>

    <div class="head-row">
      <div>
        <h1>{{ place.name }}</h1>
        <p class="subtitle">{{ place.categoryLabel }} · {{ place.distanceKm }} km away</p>
      </div>
      <ConditionBadge :badge="place.badge" />
    </div>

    <hr class="divider" />

    <div class="map-card">
      <div class="grid-line h" style="top: 33%" />
      <div class="grid-line h" style="top: 66%" />
      <div class="grid-line v" style="left: 35%" />
      <div class="grid-line v" style="left: 71%" />
      <svg class="map-route" viewBox="0 0 327 108">
        <circle cx="75" cy="71" r="3.5" fill="#888780" />
        <text x="75" y="88" font-size="9" fill="#888780" text-anchor="middle">You</text>
        <line x1="80" y1="66" x2="235" y2="23" stroke="#639922" stroke-width="1.3" stroke-dasharray="3 3" />
        <path d="M235 14 C235 10 238 7 241 7 C244 7 247 10 247 14 C247 18 241 25 241 25 C241 25 235 18 235 14 Z" fill="#3B6D11" />
        <circle cx="241" cy="14" r="2.5" fill="#F1EFE8" />
      </svg>
    </div>
    <p class="map-caption">{{ place.distanceKm }} km, straight-line distance</p>

    <p class="section-label" style="margin-top: 20px">On-site duration</p>
    <p class="duration-main">{{ store.planMin }}-minute on-site plan</p>
    <p class="duration-sub">Matches your {{ store.durationMin }}-min request · excludes travel</p>

    <hr class="divider" />

    <p class="section-label">Conditions when you go</p>
    <p v-for="c in place.conditions" :key="c.text" class="condition-row">
      <span class="condition-icon">
        <svg v-if="c.icon === 'sun'" width="12" height="12" viewBox="0 0 12 12">
          <circle cx="6" cy="6" r="2.2" fill="none" stroke="#27500A" stroke-width="1" />
          <path d="M6 3 v-1.3 M6 9 v1.3 M3 6 h-1.3 M9 6 h1.3" stroke="#27500A" stroke-width="1" />
        </svg>
        <svg v-else-if="c.icon === 'uv'" width="12" height="12" viewBox="0 0 12 12">
          <path d="M2 10 L6 2 L10 10" fill="none" stroke="#27500A" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg v-else-if="c.icon === 'wind'" width="12" height="12" viewBox="0 0 12 12">
          <line x1="1" y1="3" x2="11" y2="3" stroke="#854F0B" stroke-width="1.3" stroke-linecap="round" />
          <line x1="1" y1="6.5" x2="8" y2="6.5" stroke="#854F0B" stroke-width="1.3" stroke-linecap="round" />
          <line x1="1" y1="10" x2="10" y2="10" stroke="#854F0B" stroke-width="1.3" stroke-linecap="round" />
        </svg>
        <svg v-else width="12" height="12" viewBox="0 0 12 12">
          <path d="M2 6 l3 3 l6 -7" fill="none" stroke="#27500A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </span>
      {{ c.text }}
    </p>

    <hr class="divider" />

    <p class="section-label">Why this appears in your top 3</p>
    <ul class="why-list">
      <li v-for="r in place.reasons" :key="r">{{ r }}</li>
    </ul>

    <hr class="divider" />

    <p class="section-label">What to expect</p>
    <p class="expect">{{ place.expect }}</p>

    <div class="disclaimer">
      Candidate activity opportunity — opening hours, cost and accessibility aren't available yet.
    </div>

    <div class="btn-row" style="margin-top: 20px">
      <button class="btn btn-secondary" @click="$router.back()">Back</button>
      <button class="btn btn-primary" @click="getDirections">Get directions</button>
    </div>
  </template>

  <template v-else>
    <div class="app-bar">
      <button class="back-btn" aria-label="Back" @click="$router.push('/results')">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <span class="crumb">Back to your top 3</span>
    </div>
    <p class="subtitle" style="margin-top: 20px">Place not found.</p>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import ConditionBadge from '../components/ConditionBadge.vue'
import { useSearchStore } from '../store'

const props = defineProps({ id: { type: String, required: true } })
const store = useSearchStore()
const place = computed(() => store.place(props.id))

function getDirections() {
  // Demo handoff: opens the public maps search for the place name.
  const q = encodeURIComponent(`${place.value.name}, VIC`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank')
}
</script>

<style scoped>
.crumb {
  font-size: 13px;
  color: var(--ink-3);
}

.head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

.map-card {
  height: 108px;
  border-radius: 14px;
  background: var(--paper);
  position: relative;
  overflow: hidden;
}

.grid-line { position: absolute; background: var(--line-2); }
.grid-line.h { left: 0; right: 0; height: 1px; }
.grid-line.v { top: 0; bottom: 0; width: 1px; }

.map-route { position: absolute; inset: 0; width: 100%; height: 100%; }

.map-caption {
  text-align: center;
  font-size: 10.5px;
  color: var(--ink-4);
  margin-top: 10px;
}

.duration-main {
  font-size: 15px;
  font-weight: 500;
}

.duration-sub {
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 4px;
}

.condition-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12.5px;
  margin-bottom: 10px;
}

.condition-icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--green-light);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.why-list {
  list-style: none;
}

.why-list li {
  font-size: 11.5px;
  color: var(--ink-2);
  padding-left: 14px;
  position: relative;
  margin-bottom: 8px;
}

.why-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 5px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--green);
}

.expect {
  font-size: 11.5px;
  color: var(--ink-2);
  line-height: 1.5;
}

.disclaimer {
  margin-top: 14px;
  border-radius: 10px;
  background: var(--paper);
  padding: 12px 16px;
  font-size: 10.5px;
  color: var(--ink-3);
  line-height: 1.45;
}
</style>
