<template>
  <template v-if="mission && missionStore.status === 'in_progress'">
    <div class="app-bar">
      <button class="back-btn" aria-label="Back to preview" @click="router.push('/plan')">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <span class="page-title">Mission run</span>
      <span class="spacer" />
    </div>

    <div class="scroll-area run-scroll">
      <h1 class="mission-name">{{ mission.title }}</h1>
      <div class="progress-track">
        <div v-for="(state, i) in missionStore.stepStates" :key="i" class="seg" :class="{ active: state === 'active' }">
          <span :style="{ width: state === 'done' ? '100%' : state === 'active' ? '50%' : '0%' }" />
        </div>
      </div>
      <p class="step-count">Step {{ missionStore.stepIndex + 1 }} of {{ missionStore.totalSteps }}</p>

      <div class="step-display">
        <p class="step-big">{{ missionStore.currentStep.title }}</p>
        <span class="badge muted">{{ missionStore.currentStep.confirm === 'photo' ? 'Photo check' : 'Tap to confirm' }}</span>
      </div>

      <button class="link-btn overview-link" @click="router.push('/plan/overview')">Overview</button>
    </div>

    <hr class="divider" style="margin-bottom: 16px" />
    <div class="btn-row">
      <button class="btn btn-secondary" @click="advance">Skip</button>
      <button class="btn btn-primary" @click="advance">Confirm</button>
    </div>
  </template>

  <template v-else>
    <AppHeader plain />
    <div class="scroll-area placeholder">
      <p class="section-eyebrow">Plan</p>
      <h1>No mission running</h1>
      <p class="subtitle">Start one from Today, or preview and start it here.</p>
      <button class="btn btn-secondary" style="margin-top: 16px" @click="router.push('/plan')">Go to Plan</button>
    </div>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'

const router = useRouter()
const missionStore = useMissionStore()
const mission = computed(() => missionStore.active)

function advance() {
  missionStore.advanceStep()
  if (missionStore.status === 'done') router.push('/plan/finished')
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

.run-scroll { display: flex; flex-direction: column; }

.mission-name { color: var(--green-dark); margin-bottom: 16px; }

.step-count {
  margin-top: 10px;
  font-size: 11.5px;
  color: var(--ink-4);
}

.step-display {
  margin-top: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 14px;
}

.step-big {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.35;
}

.overview-link {
  margin: 32px auto 0;
  display: block;
}

.link-btn {
  background: none;
  border: none;
  color: var(--green-dark);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
}

.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; }
</style>
