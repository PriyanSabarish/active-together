<template>
  <AppHeader />

  <div class="scroll-area">
    <button class="pill crumb" @click="router.push('/you')">‹ Preferences</button>
    <h1 style="margin-top: 14px">How old is Daniel?</h1>
    <p class="subtitle">Stored as a band only, never a date of birth.</p>

    <button
      v-for="band in AGE_BANDS"
      :key="band.id"
      class="band-row"
      :class="{ on: selected === band.id }"
      @click="selected = band.id"
    >
      <span>{{ band.label }}</span>
      <span class="check" :class="{ on: selected === band.id }" />
    </button>

    <div class="note-card">{{ selectedBand.note }}</div>
  </div>

  <button class="btn btn-primary" style="width: 100%; margin-top: 14px" @click="save">Save age band</button>
</template>

<script setup>
// Age band picker. Stored as a band only, never a date of birth. The three
// bands are defined once in preferencesStore.js.

import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { AGE_BANDS, usePreferencesStore } from '../preferencesStore'

const router = useRouter()
const prefs = usePreferencesStore()

const selected = ref(prefs.ageBand)
const selectedBand = computed(() => AGE_BANDS.find((b) => b.id === selected.value) ?? AGE_BANDS[0])

function save() {
  prefs.setAgeBand(selected.value)
  router.push('/you')
}
</script>

<style scoped>
.page-title {
  flex: 1;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-3);
}

.spacer { width: 26px; flex-shrink: 0; }

.band-row {
  width: 100%;
  height: 52px;
  border: none;
  border-radius: var(--radius-field);
  background: var(--card);
  box-shadow: var(--shadow-card);
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  margin-top: 12px;
}

.band-row.on {
  background: var(--green);
  color: var(--paper);
  box-shadow: var(--shadow-selected);
  font-weight: 600;
}

.check {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1.5px solid var(--line-3);
  flex-shrink: 0;
}

.check.on {
  border-color: var(--paper);
  background: var(--paper);
  position: relative;
}

.check.on::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 9px;
  border: solid var(--green);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.note-card { margin-top: 20px; }
</style>
