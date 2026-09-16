<template>
  <AppHeader />
  <div class="scroll-area">
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
      <button class="btn btn-primary start-btn" @click="start">See the mission <span class="btn-arrow">→</span></button>
    </article>

    <div class="stat-grid" style="margin-top: 18px">
      <button class="stat-tile primary as-btn" @click="$router.push('/insights')">
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
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'
import { useHistoryStore, feedbackEmoji, feedbackLabel, relativeDayLabel } from '../historyStore'

const router = useRouter()
const missionStore = useMissionStore()
const historyStore = useHistoryStore()

// "Recommended for today" has no real ranking yet (that's a later phase) —
// just offer the first mock candidate so the card has something to show.
const todayMission = computed(() => missionStore.candidates[0])
const reason = "Matches Daniel's preference and hasn't been used in the last 5 outings."

// F21 — real counts and feedback, once F19/F20 have written any records.
const thisWeekCount = computed(() => historyStore.thisWeekCount)
const lastWeekCount = computed(() => historyStore.lastWeekCount)
const lastFeedback = computed(() => {
  const r = historyStore.mostRecent
  if (!r || !r.feedback) return null
  return { emoji: feedbackEmoji(r.feedback), label: feedbackLabel(r.feedback), when: relativeDayLabel(r.date) }
})

function start() {
  missionStore.chooseMission(todayMission.value.id)
  router.push('/plan')
}
</script>

<style scoped>
.mission-card {
  margin-top: 18px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 16px;
}

.mission-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.mission-title { font-family: var(--font-display); font-size: 18px; font-weight: 600; letter-spacing: -0.2px; }
.mission-meta { font-size: 13px; color: var(--ink-3); margin-top: 3px; }

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

.as-btn { border: none; text-align: left; font-family: inherit; cursor: pointer; }
</style>
