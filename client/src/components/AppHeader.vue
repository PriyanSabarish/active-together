<template>
  <div>
    <div class="app-bar">
      <button v-if="back" class="back-btn" aria-label="Back" @click="$router.back()">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <RouterLink to="/play" class="brand-link" aria-label="Go to Play">
        <svg class="logo-pin" width="26" height="32" viewBox="0 0 100 126" aria-hidden="true">
          <path d="M50 2 C23 2 4 22 4 48 C4 82 50 124 50 124 C50 124 96 82 96 48 C96 22 77 2 50 2 Z" class="pin-body" />
          <circle cx="50" cy="34" r="12" class="pin-eye" />
          <path d="M28 54 Q50 70 72 54" fill="none" class="pin-smile" stroke-width="10" stroke-linecap="round" />
          <path d="M32 78 Q50 92 68 78" fill="none" class="pin-smile-2" stroke-width="10" stroke-linecap="round" />
        </svg>
        <span class="app-name"><b class="w-active">Active</b> <b class="w-together">Together</b><b class="w-dot">.</b></span>
      </RouterLink>
      <span class="grow" />
      <!-- Right slot: defaults to the weather pill, screens can override. -->
      <slot name="right">
        <span v-if="weatherPill" class="wx-pill">{{ weatherPill }}</span>
      </slot>
    </div>
    <div v-if="!plain" class="progress-track" aria-label="Progress">
      <div v-for="i in total" :key="i" class="seg">
        <span :style="{ width: i <= step ? '100%' : '0%' }" />
      </div>
    </div>
  </div>
</template>

<script setup>
// Top bar shared by every screen: logo (links to Play), optional back arrow,
// and a weather pill on the right once /data/context has returned for the
// current starting point. Funnel step dots are opt-in via `plain=false`.

import { computed } from 'vue'
import { useSearchStore } from '../store'

defineProps({
  step: { type: Number, default: 0 },
  total: { type: Number, default: 3 },
  back: { type: Boolean, default: false },
  // Tab-root screens show just the logo bar, no funnel step dots.
  plain: { type: Boolean, default: true }
})

// Right-hand weather pill, as in the Canvas header. Only shows once the
// context call has returned something usable for the current location.
const store = useSearchStore()
const weatherPill = computed(() => {
  const w = store.weather
  if (!w || w.available === false || w.temp_c == null) return ''
  const rain = w.precip_prob == null ? null : Math.round(w.precip_prob * 100)
  const temp = `${Math.round(w.temp_c)}°`
  if (rain == null) return temp
  if (rain >= 50) return `${temp}, rain likely`
  if (rain >= 25) return `${temp}, some rain`
  return `${temp}, clear`
})
</script>

<style scoped>
.brand-link {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}

.grow { flex: 1; }
.logo-pin { flex-shrink: 0; }
.progress-track { margin-bottom: 28px; }

.pin-body { fill: var(--green); }
.pin-eye { fill: var(--accent); }
.pin-smile { stroke: var(--paper); }
.pin-smile-2 { stroke: #9FCC86; }

.app-name b { font-weight: 600; }
.w-active { color: var(--green); }
.w-together { color: var(--ink); }
.w-dot { color: var(--accent); }

.wx-pill {
  height: 28px;
  padding: 0 11px;
  border-radius: var(--radius-pill);
  background: rgba(47, 107, 54, 0.1);
  color: var(--green);
  font-size: 12.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
}

/* dark screen variant */
.phone.dark .pin-body { fill: var(--paper); }
.phone.dark .pin-smile { stroke: var(--dark); }
.phone.dark .pin-smile-2 { stroke: var(--dark); }
.phone.dark .pin-eye { fill: var(--accent); }
.phone.dark .w-active,
.phone.dark .w-together { color: rgba(242, 241, 236, 0.85); }
.phone.dark .wx-pill { background: rgba(242, 241, 236, 0.1); color: rgba(242, 241, 236, 0.85); }
</style>
