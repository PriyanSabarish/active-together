<template>
  <div class="app-bar">
    <button class="back-btn" aria-label="Back" @click="router.back()">
      <svg width="18" height="24" viewBox="0 0 18 24">
        <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
    <span class="page-title">Pick a mission</span>
    <span class="spacer" />
  </div>

  <div class="scroll-area">
    <h1>Which one today?</h1>
    <p class="subtitle">Read these out loud for Daniel to choose — nothing is picked yet.</p>

    <button
      v-for="option in missionStore.candidates"
      :key="option.id"
      class="option-card"
      :class="{ on: selectedId === option.id }"
      @click="selectedId = option.id"
    >
      <div class="option-top">
        <p class="option-title">{{ option.title }}</p>
        <span class="badge mission">{{ option.steps.length }}-step mission</span>
      </div>
      <p class="option-meta">{{ option.placeName }} · about {{ option.durationMin }} min</p>
    </button>
  </div>

  <hr class="divider" style="margin-bottom: 16px" />
  <button class="btn btn-primary" style="width: 100%" :disabled="!selectedId" @click="confirm">
    Choose this mission
  </button>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMissionStore } from '../missionStore'

const router = useRouter()
const missionStore = useMissionStore()
const selectedId = ref(null) // deliberately unset — nothing is pre-selected

function confirm() {
  if (!selectedId.value) return
  missionStore.chooseMission(selectedId.value)
  missionStore.startMission()
  router.push('/plan/run')
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

.option-card {
  width: 100%;
  margin-top: 14px;
  border: 1px solid var(--line-2);
  border-radius: 14px;
  padding: 16px;
  background: #FFFFFF;
  text-align: left;
  font-family: inherit;
  cursor: pointer;
}

.option-card.on {
  border-color: var(--green);
  background: var(--green-light);
}

.option-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.option-title { font-size: 14.5px; font-weight: 500; }
.option-meta { font-size: 11.5px; color: var(--ink-3); margin-top: 6px; }

.btn-primary:disabled { opacity: 0.45; cursor: default; }
</style>
