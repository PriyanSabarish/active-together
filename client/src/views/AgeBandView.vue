<template>
  <div class="app-bar">
    <button class="back-btn" aria-label="Back to preferences" @click="router.push('/prefs')">
      <svg width="18" height="24" viewBox="0 0 18 24">
        <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
    <span class="page-title">Age band</span>
    <span class="spacer" />
  </div>

  <div class="scroll-area">
    <h1>How old is Daniel?</h1>
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

  <hr class="divider" style="margin-bottom: 16px" />
  <button class="btn btn-primary" style="width: 100%" @click="save">Save age band</button>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AGE_BANDS, usePreferencesStore } from '../preferencesStore'

const router = useRouter()
const prefs = usePreferencesStore()

const selected = ref(prefs.ageBand)
const selectedBand = computed(() => AGE_BANDS.find((b) => b.id === selected.value) ?? AGE_BANDS[0])

function save() {
  prefs.setAgeBand(selected.value)
  router.push('/prefs')
}
</script>

<style scoped>
.page-title {
  flex: 1;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-3);
}

.spacer { width: 26px; flex-shrink: 0; }

.band-row {
  width: 100%;
  height: 52px;
  border: 1px solid var(--line-3);
  border-radius: 10px;
  background: #FFFFFF;
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
  background: var(--green-light);
  border-color: var(--green);
  font-weight: 500;
}

.check {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1.5px solid var(--line-3);
  flex-shrink: 0;
}

.check.on {
  border-color: var(--green);
  background: var(--green);
  position: relative;
}

.check.on::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 5px;
  height: 9px;
  border: solid #FFFFFF;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.note-card { margin-top: 20px; }
</style>
