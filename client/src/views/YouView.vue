<template>
  <AppHeader />
  <div class="scroll-area">
    <h1>What does Daniel like?</h1>
    <p class="subtitle">Optional. Tap to set each one — change it any time.</p>

    <!-- One row per backend category with a three-way choice: likes / no preference /
         not for me. Stored as an affinity (80 / 50 / 20) so the recommender can weight it. -->
    <div v-for="(meta, key) in CATEGORY_META" :key="key" class="pref-row" :class="degreeClass(prefs.affinities[key])">
      <span class="glyph">{{ meta.label.charAt(0) }}</span>
      <span class="pref-label">{{ meta.label }}</span>
      <span class="tri" role="radiogroup" :aria-label="meta.label">
        <button
          v-for="o in OPTIONS"
          :key="o.id"
          type="button"
          class="tri-btn"
          :class="[o.id, { on: degreeClass(prefs.affinities[key]) === o.id }]"
          :title="o.label"
          :aria-label="o.label"
          role="radio"
          :aria-checked="degreeClass(prefs.affinities[key]) === o.id"
          @click="prefs.setAffinity(key, o.value)"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="o.icon" /></svg>
        </button>
      </span>
    </div>

    <h2 class="sect">Age band</h2>
    <button class="info-card as-btn" @click="router.push('/you/age-band')">
      <span class="info-title">{{ prefs.ageBandInfo.label }}</span>
      <span class="info-body">{{ prefs.ageBandInfo.note }}</span>
      <span class="change-link">Change ›</span>
    </button>

    <button class="info-card as-btn" style="margin-top: 10px" @click="toggleDemo">
      <span class="info-title">Demo data</span>
      <span class="info-body">{{ demoOn ? 'Week and You show sample outings and preferences.' : 'Off — Week starts empty until a mission is finished.' }}</span>
      <span class="change-link">{{ demoOn ? 'Turn off' : 'Turn on' }}</span>
    </button>

    <button class="btn btn-outline replay" @click="replayIntro">Replay the intro</button>
  </div>
</template>

<script setup>
// You tab: a three-way like / neutral / not-for-me choice per category, age
// band, the demo-data switch and a way to replay the intro. Preferences are
// device-local and, in this iteration, not yet read by the recommender.

import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { CATEGORY_META } from '../store'
import { usePreferencesStore } from '../preferencesStore'
import { demoEnabled, setDemoEnabled } from '../demoSeed'
import { ref } from 'vue'

const router = useRouter()
const prefs = usePreferencesStore()

// Three-way choice, stored as an affinity so the recommender can weight it.
const OPTIONS = [
  { id: 'likes', label: 'Likes', value: 80, icon: 'M7 10v11 M15 5.9 14 10h5.8a2 2 0 0 1 1.9 2.6l-2.3 7a2 2 0 0 1-1.9 1.4H7V10l4.5-6.2a1.6 1.6 0 0 1 3 .9l.5 1.2Z' },
  { id: 'neutral', label: 'No preference', value: 50, icon: 'M5 12h14' },
  { id: 'nope', label: 'Not for me', value: 20, icon: 'M17 14V3 M9 18.1 10 14H4.2a2 2 0 0 1-1.9-2.6l2.3-7A2 2 0 0 1 6.5 3H17v11l-4.5 6.2a1.6 1.6 0 0 1-3-.9l-.5-1.2Z' }
]

// 0-100 affinity -> which of the three is lit.
function degreeClass(v) {
  if (v >= 67) return 'likes'
  if (v >= 34) return 'neutral'
  return 'nope'
}

const demoOn = ref(demoEnabled())

// Demo data is seeded at boot, so flipping it reloads the app.
function toggleDemo() {
  setDemoEnabled(!demoOn.value)
  window.location.assign('/week')
}

// The walkthrough is gated on a localStorage flag in App.vue; clearing it and
// reloading is the simplest way to see it again.
function replayIntro() {
  try {
    localStorage.removeItem('at-onboarded-v1')
    sessionStorage.removeItem('at-admin-authed') // the intro is shown right after the gate
  } catch {
    /* storage unavailable */
  }
  window.location.assign('/')
}
</script>

<style scoped>
.pref-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 9px 9px 14px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.pref-row:first-of-type { margin-top: 18px; }
.pref-row.likes { box-shadow: inset 0 0 0 1.5px var(--green), var(--shadow-card); }
.pref-row.nope { box-shadow: inset 0 0 0 1.5px rgba(232, 145, 58, 0.55), var(--shadow-card); }

.glyph {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--tint);
  color: var(--ink-2);
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pref-row.likes .glyph { background: var(--green-light); color: var(--green); }
.pref-row.nope .glyph { background: var(--amber-light); color: var(--amber); }

.pref-label { flex: 1; min-width: 0; font-size: 15.5px; font-weight: 500; }

.tri { display: inline-flex; gap: 4px; padding: 3px; border-radius: 13px; background: rgba(30, 42, 31, 0.055); }

.tri-btn {
  width: 44px;
  height: 38px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--ink-4);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.16s ease;
}

.tri-btn.on.likes { background: var(--green); color: var(--paper); }
.tri-btn.on.neutral { background: rgba(30, 42, 31, 0.28); color: var(--paper); }
.tri-btn.on.nope { background: var(--amber); color: var(--paper); }

.sect { margin-top: 24px; margin-bottom: 10px; }

.info-card {
  width: 100%;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 14px 16px;
  text-align: left;
  position: relative;
}

.as-btn { border: none; font-family: inherit; color: var(--ink); cursor: pointer; display: flex; flex-direction: column; }

.info-title { display: block; font-size: 15px; font-weight: 600; }
.info-body { display: block; font-size: 13px; color: var(--ink-3); line-height: 1.5; margin-top: 3px; padding-right: 64px; }
.change-link { position: absolute; right: 16px; top: 15px; font-size: 13.5px; font-weight: 600; color: var(--green); }

.replay { width: 100%; margin-top: 16px; }
</style>
