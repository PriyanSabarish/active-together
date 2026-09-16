<template>
  <template v-if="mission">
    <AppHeader />

    <div class="scroll-area">
      <button class="pill crumb" @click="router.push('/play')">‹ Play</button>
      <div class="head-row" style="margin-top: 14px">
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

      <p class="eyebrow-accent" style="margin-top: 20px">Equipment</p>
      <p class="body-text">{{ mission.equipment }}</p>

      <p class="eyebrow-accent" style="margin-top: 20px">Why this mission</p>
      <p class="body-text">{{ mission.whyThisMission }}</p>

      <p class="switch-link">
        Not the right fit?
        <button class="link-btn" @click="router.push('/play/pick')">Let Daniel choose instead</button>
      </p>
    </div>

    <button class="btn btn-primary" style="width: 100%; margin-top: 14px" @click="start">Start mission</button>
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area placeholder">
      <p class="eyebrow-accent">Play</p>
      <h1>No mission chosen yet</h1>
      <p class="subtitle">Take today’s pick on Play, or let Daniel choose one.</p>
      <div class="btn-row" style="width: 100%">
        <button class="btn btn-secondary" @click="router.push('/play')">Play</button>
        <button class="btn btn-primary" @click="router.push('/play/pick')">Pick a mission</button>
      </div>
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
  router.push('/play/run')
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

.head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.mission-name { color: var(--ink); }

.step-card {
  margin-top: 12px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.step-num {
  width: 28px;
  height: 28px;
  font-family: var(--font-display);
  border-radius: 50%;
  background: var(--green);
  color: var(--paper);
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
  font-weight: 600;
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
