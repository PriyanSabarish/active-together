<template>
  <AppHeader back />

  <div class="scroll-area">
    <h2>Pick a mission</h2>
    <p class="subtitle">Read these out. Daniel picks — the phone stays with you.</p>

    <button
      v-for="option in missionStore.candidates"
      :key="option.id"
      class="option-card"
      :class="{ on: selectedId === option.id }"
      @click="selectedId = option.id"
    >
      <div class="option-top">
        <span class="option-title">{{ option.title }}</span>
        <span class="option-meta">{{ option.steps.length }} tasks · {{ option.durationMin }} min</span>
      </div>
      <p class="option-line">{{ option.placeName }} · {{ option.equipment }}</p>
    </button>
  </div>

  <button class="btn btn-primary cta" :disabled="!selectedId" @click="confirm">
    {{ selected ? `Start ${selected.title.toLowerCase()}` : 'Pick one to start' }}
  </button>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'

const router = useRouter()
const missionStore = useMissionStore()
const selectedId = ref(null) // deliberately unset — nothing is pre-selected
const selected = computed(() => missionStore.candidates.find((m) => m.id === selectedId.value) ?? null)

function confirm() {
  if (!selectedId.value) return
  missionStore.chooseMission(selectedId.value)
  missionStore.startMission()
  router.push('/plan/run')
}
</script>

<style scoped>
h2 { margin-top: 4px; }

.option-card {
  width: 100%;
  margin-top: 12px;
  border: none;
  border-radius: var(--radius-card);
  padding: 15px 18px;
  background: var(--card);
  box-shadow: var(--shadow-card);
  color: var(--ink);
  text-align: left;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.18s ease;
}

.option-card.on {
  background: var(--green);
  color: var(--paper);
  box-shadow: 0 10px 24px rgba(47, 107, 54, 0.24);
}

.option-top { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.option-title { font-family: var(--font-display); font-size: 17.5px; font-weight: 600; letter-spacing: -0.2px; }
.option-meta { font-size: 13px; font-weight: 600; color: var(--ink-4); white-space: nowrap; }
.option-card.on .option-meta { color: var(--accent); }
.option-line { font-size: 13.5px; color: var(--ink-3); margin-top: 4px; line-height: 1.4; }
.option-card.on .option-line { color: rgba(242, 241, 236, 0.75); }

.cta { width: 100%; margin-top: 14px; }
</style>
