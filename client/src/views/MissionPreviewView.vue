<template>
  <template v-if="mission">
    <div class="app-bar">
      <button class="back-btn" aria-label="Back to Today" @click="router.push('/today')">
        <svg width="18" height="24" viewBox="0 0 18 24">
          <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <span class="page-title">Mission preview</span>
      <span class="spacer" />
    </div>

    <div class="scroll-area">
      <div class="head-row">
        <div>
          <h1 class="mission-name">{{ mission.title }}</h1>
          <p class="subtitle">{{ mission.placeName }} · {{ mission.steps.length }} steps · about {{ mission.durationMin }} min</p>
        </div>
        <span class="badge muted">Ages {{ mission.ageBand }}</span>
      </div>

      <div class="tip-banner" style="margin-top: 16px">All steps shown below — nothing hidden.</div>

      <article v-for="(step, i) in mission.steps" :key="i" class="step-card">
        <span class="step-num">{{ i + 1 }}</span>
        <div>
          <p class="step-title">{{ step.title }}</p>
          <span class="badge muted step-confirm">{{ step.confirm === 'photo' ? 'Photo check' : 'Tap to confirm' }}</span>
        </div>
      </article>

      <p class="section-eyebrow" style="margin-top: 20px">Equipment</p>
      <p class="body-text">{{ mission.equipment }}</p>

      <p class="section-eyebrow" style="margin-top: 20px">Why this mission</p>
      <p class="body-text">{{ mission.whyThisMission }}</p>

      <p class="switch-link">
        Not the right fit?
        <button class="link-btn" @click="router.push('/plan/pick')">Let Daniel choose instead</button>
      </p>
    </div>

    <hr class="divider" style="margin-bottom: 16px" />
    <button class="btn btn-primary" style="width: 100%" @click="start">Start mission</button>
  </template>

  <template v-else>
    <AppHeader plain />
    <div class="scroll-area placeholder">
      <p class="section-eyebrow">Plan</p>
      <h1>No mission chosen yet</h1>
      <p class="subtitle">Pick one from Today, or choose one yourself.</p>
      <button class="btn btn-secondary" style="margin-top: 16px" @click="router.push('/plan/pick')">Pick a mission</button>
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

function start() {
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

.head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.mission-name { color: var(--green-dark); }

.step-card {
  margin-top: 12px;
  border: 1px solid var(--line-2);
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--green);
  color: #FFFFFF;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-title { font-size: 13.5px; }
.step-confirm { margin-top: 6px; }

.body-text { font-size: 12.5px; color: var(--ink-2); line-height: 1.5; }

.switch-link {
  margin-top: 20px;
  font-size: 12px;
  color: var(--ink-3);
  text-align: center;
}

.link-btn {
  background: none;
  border: none;
  color: var(--green-dark);
  font-size: 12px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  padding: 0;
  margin-left: 2px;
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
