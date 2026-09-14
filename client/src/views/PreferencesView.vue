<template>
  <AppHeader plain />
  <div class="scroll-area">
    <p class="section-eyebrow">Prefs</p>
    <h1>Daniel's preferences</h1>
    <p class="subtitle">Set once, used every time.</p>

    <div v-for="(meta, key) in CATEGORY_META" :key="key" class="affinity-row">
      <div class="affinity-top">
        <span class="affinity-label">{{ meta.label }}</span>
        <span class="affinity-degree">{{ degreeLabel(prefs.affinities[key]) }}</span>
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

    <hr class="divider" />

    <p class="section-label">Age band</p>
    <button class="age-row" @click="router.push('/prefs/age-band')">
      <span class="age-value">{{ prefs.ageBandInfo.label }}</span>
      <span class="change-link">Change</span>
    </button>
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
  if (v >= 67) return 'Loves it'
  if (v >= 34) return 'Some interest'
  return 'Not really'
}
</script>

<style scoped>
.affinity-row { margin-top: 22px; }

.affinity-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.affinity-label { font-size: 13.5px; font-weight: 500; }
.affinity-degree { font-size: 11.5px; color: var(--green-dark); }

.affinity-slider {
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  height: 4px;
  border-radius: 2px;
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
  background: #FFFFFF;
  border: 2.5px solid var(--green);
  cursor: pointer;
}

.affinity-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 2.5px solid var(--green);
  cursor: pointer;
}

.age-row {
  width: 100%;
  height: 48px;
  border: 1px solid var(--line-3);
  border-radius: 10px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-family: inherit;
  cursor: pointer;
}

.age-value { font-size: 13.5px; }
.change-link { font-size: 13px; font-weight: 500; color: var(--green-dark); }
</style>
