<template>
  <template v-if="mission && missionStore.status === 'in_progress'">
    <AppHeader />

    <div class="scroll-area run-scroll">
      <div class="run-head">
        <span class="run-title">{{ mission.title }}</span>
        <button class="run-count" @click="showAll = !showAll">
          Task {{ missionStore.stepIndex + 1 }} of {{ missionStore.totalSteps }}
          <span class="caret">{{ showAll ? '▴' : '▾' }}</span>
        </button>
      </div>

      <div class="run-track">
        <span v-for="(state, i) in missionStore.stepStates" :key="i" class="run-seg" :class="state" />
      </div>

      <!-- Full task list, toggled from the counter; done steps are struck through. -->
      <div v-if="showAll" class="all-tasks">
        <div v-for="(step, i) in mission.steps" :key="i" class="task-row" :class="missionStore.stepStates[i]">
          <span class="task-num">{{ missionStore.stepStates[i] === 'done' ? '✓' : i + 1 }}</span>
          <span class="task-text">{{ step.title }}</span>
        </div>
      </div>

      <!-- The one task to read out. Large type on purpose: the phone stays with the parent. -->
      <div class="step-card">
        <!-- Sketch: a small line drawing keyed to the task's icon. -->
        <div class="sketch" aria-hidden="true">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path :d="taskIcon(missionStore.currentStep.icon)" /></svg>
        </div>
        <h1 class="step-big">{{ missionStore.currentStep.title }}</h1>
        <p class="step-hint">{{ isLast ? 'Last one. Then head back.' : 'Read it out. No rush.' }}</p>
      </div>

      <button class="btn btn-accent" @click="advance">{{ isLast ? 'Finish mission' : 'Done' }}</button>
      <button class="btn skip-btn" @click="advance">Skip this one</button>

      <!-- Giving up ends the mission without a history record (AC-8.1.4); the note is the warning. -->
      <button class="giveup" @click="abandon">← Give up this mission</button>
      <p class="offline-note">Nothing is logged if you stop now.</p>
    </div>
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area placeholder">
      <p class="eyebrow-accent">Play</p>
      <h1>No mission running</h1>
      <p class="subtitle">Pick a place on Play, then start a mission from there.</p>
      <button class="btn btn-outline" style="margin-top: 16px" @click="router.push('/play')">Go to Play</button>
    </div>
  </template>
</template>

<script setup>
// Mission in progress, on the dark shell (route.meta.dark). One task at a
// time in large type; Done and Skip both advance (nothing is a fail). The
// task counter toggles the full list. "Give up this mission" ends it on the
// spot without logging it as complete; the note underneath is the warning.

import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'
import { taskIcon } from '../taskIcons'

const router = useRouter()
const missionStore = useMissionStore()
const mission = computed(() => missionStore.active)
const showAll = ref(false)
const isLast = computed(() => missionStore.stepIndex === missionStore.totalSteps - 1)

function abandon() {
  missionStore.abandonMission()
  router.push('/play')
}

function advance() {
  missionStore.advanceStep()
  if (missionStore.status === 'done') router.push('/play/finished')
}
</script>

<style scoped>
.run-scroll { display: flex; flex-direction: column; }

.run-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.run-title { font-size: 14px; font-weight: 600; color: rgba(242, 241, 236, 0.6); flex: 1; }

.run-count {
  background: none;
  border: none;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--accent);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.caret { font-size: 11px; }

.run-track { display: flex; gap: 6px; margin-top: 10px; }
.run-seg { flex: 1; height: 5px; border-radius: 3px; background: rgba(242, 241, 236, 0.22); }
.run-seg.done, .run-seg.active { background: var(--accent); }

.all-tasks {
  margin-top: 14px;
  border-radius: 15px;
  background: rgba(242, 241, 236, 0.06);
  padding: 6px 12px;
}

.task-row { display: flex; align-items: center; gap: 12px; padding: 9px 0; color: rgba(242, 241, 236, 0.62); font-size: 14px; }
.task-row.done { color: rgba(242, 241, 236, 0.4); text-decoration: line-through; }
.task-row.active { color: var(--paper); }

.task-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(242, 241, 236, 0.1);
  color: rgba(242, 241, 236, 0.55);
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.task-row.active .task-num { background: var(--accent); color: var(--dark); box-shadow: 0 0 0 3px rgba(232, 145, 58, 0.2); }

.step-card {
  margin-top: 18px;
  border-radius: 24px;
  background: rgba(242, 241, 236, 0.06);
  box-shadow: inset 0 0 0 1px rgba(242, 241, 236, 0.08);
  padding: 22px 24px 24px;
}

.step-big {
  color: var(--paper);
  font-size: 30px;
  line-height: 1.15;
  letter-spacing: -0.7px;
  margin: 0;
  text-wrap: pretty;
}

.step-hint { margin-top: 14px; font-size: 15px; color: rgba(242, 241, 236, 0.55); }

.btn-accent { margin-top: 18px; width: 100%; }

.skip-btn {
  margin-top: 10px;
  width: 100%;
  height: 52px;
  background: transparent;
  color: rgba(242, 241, 236, 0.85);
  border: none;
  box-shadow: inset 0 0 0 1.5px rgba(242, 241, 236, 0.22);
}

.offline-note { margin-top: 8px; text-align: center; font-size: 12.5px; color: rgba(242, 241, 236, 0.4); line-height: 1.4; }

.sketch { color: rgba(242, 241, 236, 0.55); margin-bottom: 14px; }
.sketch svg { display: block; }

.giveup {
  display: block;
  margin: 22px auto 0;
  background: none;
  border: none;
  color: var(--paper);
  font-size: 14px;
  font-weight: 600;
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

.placeholder h1 { margin-top: 4px; color: var(--paper); }
</style>
