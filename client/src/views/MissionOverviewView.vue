<template>
  <template v-if="mission">
    <AppHeader />

    <div class="scroll-area">
      <button class="pill crumb" @click="router.push('/play/run')">‹ Back to the task</button>
      <h1 class="mission-name" style="margin-top: 14px">{{ mission.title }}</h1>
      <p class="subtitle">{{ doneCount }} of {{ missionStore.totalSteps }} steps done · about {{ minsLeft }} min left</p>

      <div class="progress-track" style="margin-top: 16px">
        <div v-for="(state, i) in missionStore.stepStates" :key="i" class="seg" :class="{ active: state === 'active' }">
          <span :style="{ width: state === 'done' ? '100%' : state === 'active' ? '50%' : '0%' }" />
        </div>
      </div>

      <article v-for="(step, i) in mission.steps" :key="i" class="step-row" :class="missionStore.stepStates[i]">
        <span class="step-icon" :class="missionStore.stepStates[i]">
          <svg v-if="missionStore.stepStates[i] === 'done'" width="14" height="14" viewBox="0 0 14 14">
            <path d="M2 7 l3.5 3.5 L12 3" fill="none" stroke="var(--paper)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <template v-else>{{ i + 1 }}</template>
        </span>
        <div>
          <p class="step-title" :class="{ muted: missionStore.stepStates[i] === 'todo' }">{{ step.title }}</p>
          <p class="step-status" :class="missionStore.stepStates[i]">
            <template v-if="missionStore.stepStates[i] === 'done'">Done · confirmed by {{ step.confirm === 'photo' ? 'photo' : 'tap' }}</template>
            <template v-else-if="missionStore.stepStates[i] === 'active'">In progress · {{ step.confirm === 'photo' ? 'photo' : 'tap' }} step</template>
            <template v-else>Not started yet</template>
          </p>
        </div>
      </article>

      <div class="note-card" style="margin-top: 16px">You can skip a step any time — nothing is a fail.</div>
    </div>

    <div class="btn-row">
      <button class="btn btn-secondary" @click="skip">Skip this step</button>
      <button class="btn btn-primary" @click="router.push('/play/run')">Back to step {{ missionStore.stepIndex + 1 }}</button>
    </div>
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area placeholder">
      <p class="eyebrow-accent">Play</p>
      <h1>No mission running</h1>
      <p class="subtitle">Start one from Play first.</p>
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

const doneCount = computed(() => missionStore.stepStates.filter((s) => s === 'done').length)
const minsLeft = computed(() => {
  const total = missionStore.totalSteps
  if (!mission.value || !total) return 0
  return Math.max(1, Math.round((mission.value.durationMin * (total - doneCount.value)) / total))
})

function skip() {
  missionStore.advanceStep()
  if (missionStore.status === 'done') router.push('/play/finished')
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

.mission-name { color: var(--ink); }

.step-row {
  margin-top: 12px;
  border-radius: var(--radius-card);
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}

.step-row.active {
  box-shadow: inset 0 0 0 1.5px var(--green), var(--shadow-card);
}

.step-icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: var(--line-2);
  color: var(--ink-4);
}

.step-icon.done { background: var(--green); color: var(--paper); }
.step-icon.active { background: var(--green-light); color: var(--green-dark); border: 1.5px solid var(--green); }

.step-title { font-size: 13.5px; font-weight: 600; }
.step-title.muted { color: var(--ink-4); font-weight: 400; }

.step-status { font-size: 11px; color: var(--ink-4); margin-top: 3px; }
.step-status.active { color: var(--green-dark); }

.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; }
</style>
