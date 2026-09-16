<template>
  <AppHeader />
  <div class="scroll-area">
    <h1>What does Daniel like?</h1>
    <p class="subtitle">Optional. Drag a slider to change it any time.</p>

    <div v-for="(meta, key) in CATEGORY_META" :key="key" class="pref-card">
      <div class="pref-top">
        <span class="glyph">{{ meta.label.charAt(0) }}</span>
        <span class="pref-label">{{ meta.label }}</span>
        <span class="pref-tag" :class="degreeClass(prefs.affinities[key])">{{ degreeLabel(prefs.affinities[key]) }}</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        step="5"
        :value="prefs.affinities[key]"
        class="affinity-slider"
        :style="{ '--fill': prefs.affinities[key] + '%' }"
        @input="prefs.setAffinity(key, $event.target.value)"
      />
    </div>

    <h2 class="sect">Age band</h2>
    <button class="info-card as-btn" @click="router.push('/prefs/age-band')">
      <span class="info-title">{{ prefs.ageBandInfo.label }}</span>
      <span class="info-body">{{ prefs.ageBandInfo.note }}</span>
      <span class="change-link">Change ›</span>
    </button>

    <div class="info-card" style="margin-top: 10px">
      <p class="info-title">Coverage</p>
      <p class="info-body">City of Melbourne, Monash and Melton. Park and playground locations come from council open data.</p>
    </div>

    <div class="info-card" style="margin-top: 10px">
      <p class="info-title">No account</p>
      <p class="info-body">Nothing to sign up for. Preferences and your week stay on this phone.</p>
    </div>

    <button class="btn btn-outline replay" @click="replayIntro">Replay the intro</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { CATEGORY_META } from '../store'
import { usePreferencesStore } from '../preferencesStore'

const router = useRouter()
const prefs = usePreferencesStore()

function degreeLabel(v) {
  if (v >= 67) return 'Likes'
  if (v >= 34) return 'No preference'
  return 'Not for me'
}

function degreeClass(v) {
  if (v >= 67) return 'likes'
  if (v >= 34) return 'neutral'
  return 'nope'
}

// The walkthrough is gated on a localStorage flag in App.vue; clearing it and
// reloading is the simplest way to see it again.
function replayIntro() {
  try {
    localStorage.removeItem('at-onboarded-v1')
  } catch {
    /* storage unavailable */
  }
  window.location.assign('/')
}
</script>

<style scoped>
.pref-card {
  margin-top: 10px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 13px 16px 14px;
}

.pref-card:first-of-type { margin-top: 18px; }

.pref-top { display: flex; align-items: center; gap: 12px; }

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

.pref-label { flex: 1; font-size: 15px; font-weight: 600; }

.pref-tag {
  padding: 5px 11px;
  border-radius: var(--radius-pill);
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
}

.pref-tag.likes { background: var(--green); color: var(--paper); }
.pref-tag.neutral { background: var(--tint); color: var(--ink-3); }
.pref-tag.nope { background: var(--amber-light); color: var(--amber); }

.affinity-slider {
  width: 100%;
  margin-top: 12px;
  appearance: none;
  -webkit-appearance: none;
  height: 5px;
  border-radius: 3px;
  background: linear-gradient(
    to right,
    var(--green) 0%,
    var(--green) var(--fill, 50%),
    var(--line-2) var(--fill, 50%),
    var(--line-2) 100%
  );
  outline: none;
}

.affinity-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--card);
  border: 2.5px solid var(--green);
  box-shadow: var(--shadow-card);
  cursor: pointer;
}

.affinity-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--card);
  border: 2.5px solid var(--green);
  cursor: pointer;
}

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
