<template>
  <div class="app-header" :class="{ floating, overlay }">
    <div class="app-bar">
      <button v-if="back" class="back-btn" aria-label="Back" @click="$router.back()">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <RouterLink to="/" class="brand-link" aria-label="Go to Start">
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
// Top bar shared by every screen: logo (links back to Start), optional back arrow,
// and a weather pill on the right once /data/context has returned for the
// current starting point. Funnel step dots are opt-in via `plain=false`.

import { computed } from 'vue'
import { useSearchStore } from '../store'

defineProps({
  step: { type: Number, default: 0 },
  total: { type: Number, default: 3 },
  back: { type: Boolean, default: false },
  // Tab-root screens show just the logo bar, no funnel step dots.
  plain: { type: Boolean, default: true },
  // Once the screen below has scrolled, the bar becomes a floating white pill (Start design).
  floating: { type: Boolean, default: false },
  // Sit over the screen instead of above it, so the content scrolls underneath (Start).
  overlay: { type: Boolean, default: false }
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
.app-header { position: relative; z-index: 3; }

/* Over the screen: the content scrolls underneath, behind a paper fade. */
.app-header.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 6;
  padding: 24px 24px 0;
  pointer-events: none; /* only the bar itself takes taps; the fade lets scrolling through */
}
.app-header.overlay::before {
  content: '';
  position: absolute;
  inset: 0 0 -14px 0; /* the fade runs 14px past the pill, as in the design */
  z-index: -1;
  background: linear-gradient(180deg, var(--paper) 0%, rgba(242, 241, 236, 0.92) 55%, rgba(242, 241, 236, 0) 100%);
}
.app-header.overlay .app-bar { pointer-events: auto; margin-bottom: 0; }

/* As in the Start design: at rest the row is 32px tall with 6px side padding and a 19px
   title. Scrolled, it grows to a 42px white capsule (5px / 12px padding, shadow) and
   the title drops to 16px. Every property has a start value so each one animates;
   the row eases over .25s and the title over .2s, as in the design. */
.app-header.overlay .app-bar {
  min-height: 32px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0);
  box-shadow: 0 10px 26px -12px rgba(30, 42, 31, 0), 0 0 0 1px rgba(30, 42, 31, 0);
  transition: padding 0.25s ease, background-color 0.25s ease, box-shadow 0.25s ease;
}
.app-header.overlay.floating .app-bar {
  padding: 5px 5px 5px 12px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 26px -12px rgba(30, 42, 31, 0.4), 0 0 0 1px rgba(30, 42, 31, 0.06);
}
.app-header.overlay .app-name { font-size: 19px; transition: font-size 0.2s ease; }
.app-header.overlay.floating .app-name { font-size: 16px; }

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

/* dark (mission run) and green (photo prompt) screen variants */
.phone.dark .pin-body,
.phone.green .pin-body { fill: var(--paper); }
.phone.dark .pin-smile,
.phone.dark .pin-smile-2 { stroke: var(--dark); }
.phone.green .pin-smile,
.phone.green .pin-smile-2 { stroke: var(--green); }
.phone.dark .pin-eye,
.phone.green .pin-eye { fill: var(--accent); }
.phone.dark .w-active,
.phone.dark .w-together,
.phone.green .w-active,
.phone.green .w-together { color: var(--paper); }
.phone.dark .wx-pill,
.phone.green .wx-pill { background: rgba(242, 241, 236, 0.1); color: rgba(242, 241, 236, 0.85); }
</style>
