<template>
  <AppHeader />
  <div class="scroll-area">
    <SubPageHead title="What does your kid like?" />
    <p class="subtitle intro">Optional. Tap to set each one — change it any time.</p>

    <!-- One row per backend category with a three-way choice: likes / no preference /
         not for me. Stored as an affinity (80 / 50 / 20) so the recommender can weight it. -->
    <div v-for="(meta, key) in CATEGORY_META" :key="key" class="pref-row" :class="degreeClass(prefs.affinities[key])">
      <span class="glyph">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(key)" /></svg>
      </span>
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
  </div>
</template>

<script setup>
// You → What does your kid like: a three-way like / neutral / not-for-me
// choice per category. Device-local.

import AppHeader from '../components/AppHeader.vue'
import SubPageHead from '../components/SubPageHead.vue'
import { CATEGORY_META } from '../store'
import { usePreferencesStore, PREF_LEVELS, levelOf } from '../preferencesStore'
import { categoryIcon, THUMB_UP, THUMB_DOWN } from '../taskIcons'

const prefs = usePreferencesStore()

const ICON = { likes: THUMB_UP, neutral: 'M6 12h12', nope: THUMB_DOWN }
const OPTIONS = PREF_LEVELS.map((l) => ({ ...l, icon: ICON[l.id] }))
const degreeClass = levelOf
</script>

<style scoped>
.intro { margin: -10px 0 18px; }

.pref-row {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 12px 12px 16px;
  background: var(--card);
  border-radius: 16px;
  box-shadow: inset 0 0 0 1.5px rgba(30, 42, 31, 0.12), 0 1px 3px rgba(30, 42, 31, 0.06);
  transition: all 0.2s ease;
}

.pref-row.likes { box-shadow: inset 0 0 0 1.5px rgba(47, 107, 54, 0.55), var(--shadow-card); }
.pref-row.nope { box-shadow: inset 0 0 0 1.5px rgba(196, 118, 30, 0.55), var(--shadow-card); }

.glyph {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(30, 42, 31, 0.07);
  color: rgba(30, 42, 31, 0.5);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.pref-row.likes .glyph { background: rgba(47, 107, 54, 0.12); color: var(--green); }
.pref-row.nope .glyph { background: rgba(196, 118, 30, 0.14); color: #A85E12; }

.pref-label { flex: 1; min-width: 0; font-size: 15.5px; font-weight: 500; }

.tri { display: inline-flex; gap: 4px; padding: 3px; border-radius: 13px; background: rgba(30, 42, 31, 0.055); box-shadow: inset 0 0 0 1px rgba(30, 42, 31, 0.07); }

.tri-btn {
  width: 44px;
  height: 38px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(30, 42, 31, 0.38);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.16s ease;
}

.tri-btn.on { color: var(--paper); }
.tri-btn.on.likes { background: var(--green); }
.tri-btn.on.neutral { background: #8D9689; }
.tri-btn.on.nope { background: #C4761E; }
</style>
