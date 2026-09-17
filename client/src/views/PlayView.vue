<template>
  <AppHeader />
  <div class="scroll-area">
    <div v-if="missionStore.lastAbandoned" class="ended-note">
      <div>
        <p class="ended-title">Ended early · not counted as complete</p>
        <p class="ended-sub">{{ missionStore.lastAbandoned.title }} · {{ missionStore.lastAbandoned.doneCount }} of {{ missionStore.lastAbandoned.totalSteps }} steps done</p>
      </div>
      <button class="ended-close" aria-label="Dismiss" @click="missionStore.clearAbandoned()">✕</button>
    </div>

    <!-- A mission is running: resume it, don't offer a new one on top. -->
    <template v-if="missionStore.status === 'in_progress'">
      <p class="eyebrow-accent">In progress</p>
      <h1>{{ active.title }}</h1>
      <p class="subtitle">{{ active.placeName }} · task {{ missionStore.stepIndex + 1 }} of {{ missionStore.totalSteps }}</p>

      <article class="mission-card">
        <div class="run-track">
          <span v-for="(state, i) in missionStore.stepStates" :key="i" class="run-seg" :class="state" />
        </div>
        <div class="mission-block">
          <p class="mission-step"><b>Now:</b> {{ missionStore.currentStep.title }}</p>
        </div>
        <button class="btn btn-accent start-btn" @click="router.push('/play/run')">Continue mission <span class="btn-arrow">→</span></button>
      </article>
    </template>

    <!-- A mission was chosen (from Start or Pick) but not started yet. -->
    <template v-else-if="active">
      <p class="eyebrow-accent">Ready to go</p>
      <h1>{{ active.title }}</h1>
      <p class="subtitle">{{ active.placeName }} · about {{ active.durationMin }} min</p>

      <article class="mission-card">
        <div class="mission-card-top">
          <p class="mission-meta">All {{ active.steps.length }} steps are shown before you start.</p>
          <span class="badge mission">{{ active.steps.length }}-task mission</span>
        </div>
        <div class="mission-block">
          <p class="mission-step"><b>First up:</b> {{ active.steps[0].title }}</p>
          <p class="mission-equip">{{ active.equipment }}</p>
        </div>
        <button class="btn btn-primary start-btn" @click="router.push('/play/preview')">See the mission <span class="btn-arrow">→</span></button>
        <button class="link-btn" @click="missionStore.resetMission()">Choose a different one</button>
      </article>
    </template>

    <!-- Nothing chosen: today's recommendation, if one has been fetched yet
         (candidates starts empty until a place's "Pick a mission" has run). -->
    <template v-else-if="todayMission">
      <p class="eyebrow-accent">Today</p>
      <h1>Ready when you are</h1>
      <p class="subtitle">{{ reason }}</p>

      <article class="mission-card">
        <div class="mission-card-top">
          <div>
            <p class="mission-title">{{ todayMission.title }}</p>
            <p class="mission-meta">{{ todayMission.placeName }} · about {{ todayMission.durationMin }} min</p>
          </div>
          <span class="badge mission">{{ todayMission.steps.length }}-task mission</span>
        </div>
        <div class="mission-block">
          <p class="mission-step"><b>First up:</b> {{ todayMission.steps[0].title }}</p>
          <p class="mission-equip">{{ todayMission.equipment }}</p>
        </div>
        <button class="btn btn-primary start-btn" @click="takeToday">See the mission <span class="btn-arrow">→</span></button>
        <button class="link-btn" @click="router.push('/play/pick')">Let Daniel choose instead</button>
      </article>
    </template>

    <!-- Nothing chosen and nothing fetched yet — no place visited this session. -->
    <template v-else>
      <p class="eyebrow-accent">Today</p>
      <h1>Ready when you are</h1>
      <p class="subtitle">Find a place first, then pick a mission for it.</p>

      <article class="mission-card">
        <button class="btn btn-primary start-btn" @click="router.push('/results')">Find a place</button>
      </article>
    </template>

    <!-- Week counts, device-local; the green tile opens the Week tab. -->
    <div class="stat-grid" style="margin-top: 18px">
      <button class="stat-tile primary as-btn" @click="router.push('/week')">
        <p class="stat-num">{{ thisWeekCount }}</p>
        <p class="stat-sub">{{ thisWeekCount === 1 ? 'outing' : 'outings' }} this week</p>
      </button>
      <div class="stat-tile">
        <p class="stat-num">{{ lastWeekCount }}</p>
        <p class="stat-sub">last week</p>
      </div>
    </div>

    <p class="section-label" style="margin-top: 22px">Daniel's most recent feedback</p>
    <div v-if="lastFeedback" class="note-card">{{ lastFeedback.emoji }} {{ lastFeedback.label }} — {{ lastFeedback.when }}</div>
    <div v-else class="note-card">No missions completed yet.</div>
  </div>
</template>

<script setup>
// Play tab root. Shows one of three cards depending on missionStore.status:
//   not chosen  -> today's recommended mission (first mock candidate for now)
//   chosen      -> "Ready to go", into the preview
//   in progress -> resume card with progress
// Plus week stats and the most recent feedback. Also surfaces the one-time
// "ended early" notice after an abandoned mission.

import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'
import { useHistoryStore, feedbackEmoji, feedbackLabel, relativeDayLabel } from '../historyStore'

const router = useRouter()
const missionStore = useMissionStore()
const historyStore = useHistoryStore()

const active = computed(() => missionStore.active)

// "Recommended for today" has no real ranking yet (that's a later phase) —
// just offer the first mock candidate so the card has something to show.
const todayMission = computed(() => missionStore.candidates[0])
const reason = "Matches Daniel's preference and hasn't been used in the last 5 outings."

const thisWeekCount = computed(() => historyStore.thisWeekCount)
const lastWeekCount = computed(() => historyStore.lastWeekCount)
const lastFeedback = computed(() => {
  const r = historyStore.mostRecent
  if (!r || !r.feedback) return null
  return { emoji: feedbackEmoji(r.feedback), label: feedbackLabel(r.feedback), when: relativeDayLabel(r.date) }
})

function takeToday() {
  missionStore.chooseMission(todayMission.value.id)
  router.push('/play/preview')
}
</script>

<style scoped>
.ended-note {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-field);
  background: var(--amber-light);
  color: var(--amber);
}

.ended-title { font-size: 13.5px; font-weight: 700; }
.ended-sub { font-size: 12.5px; margin-top: 2px; opacity: 0.85; }

.ended-close {
  margin-left: auto;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: rgba(138, 78, 17, 0.12);
  color: var(--amber);
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
}

.mission-card {
  margin-top: 18px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 16px;
}

.mission-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.mission-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; letter-spacing: -0.2px; }
.mission-meta { font-size: 13px; color: var(--ink-3); margin-top: 3px; line-height: 1.4; }

.mission-block {
  margin-top: 12px;
  background: var(--paper);
  border-radius: 13px;
  padding: 11px 13px;
}

.mission-step { font-size: 13.5px; color: var(--ink-2); line-height: 1.45; }
.mission-step b { color: var(--ink); }
.mission-equip { font-size: 12.5px; color: var(--ink-4); margin-top: 4px; }

.start-btn { width: 100%; margin-top: 14px; }

.run-track { display: flex; gap: 6px; }
.run-seg { flex: 1; height: 5px; border-radius: 3px; background: var(--line-2); }
.run-seg.done, .run-seg.active { background: var(--accent); }

.link-btn {
  display: block;
  margin: 12px auto 0;
  background: none;
  border: none;
  color: var(--green);
  font-size: 13.5px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
}

.as-btn { border: none; text-align: left; font-family: inherit; cursor: pointer; }
</style>
