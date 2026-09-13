<template>
  <AppHeader plain />
  <div class="scroll-area">
    <p class="section-eyebrow">Today</p>
    <h1>Ready when you are</h1>
    <p class="subtitle">{{ reason }}</p>

    <article class="mission-card">
      <div class="mission-card-top">
        <div>
          <p class="mission-title">{{ todayMission.title }}</p>
          <p class="mission-meta">{{ todayMission.placeName }} · about {{ todayMission.durationMin }} min</p>
        </div>
        <span class="badge mission">{{ todayMission.steps.length }}-step mission</span>
      </div>
      <button class="btn btn-primary start-btn" @click="start">Start mission</button>
    </article>

    <hr class="divider" />

    <div class="week-row">
      <div>
        <p class="stat-value">{{ thisWeekCount }}</p>
        <p class="stat-label">activities this week</p>
      </div>
      <button class="link-btn" @click="$router.push('/insights')">View week</button>
    </div>

    <p class="section-label" style="margin-top: 20px">Daniel's most recent feedback</p>
    <div class="note-card">{{ lastFeedback.emoji }} {{ lastFeedback.label }} — {{ lastFeedback.when }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'

const router = useRouter()
const missionStore = useMissionStore()

// "Recommended for today" has no real ranking yet (that's a later phase) —
// just offer the first mock candidate so the card has something to show.
const todayMission = computed(() => missionStore.candidates[0])
const reason = "Matches Daniel's preference and hasn't been used in the last 5 outings."

// This-week count and last feedback are mock until F20/F21 write real
// completion records back to a history store.
const thisWeekCount = 3
const lastFeedback = { emoji: '🙂', label: 'Fun', when: 'Yesterday' }

function start() {
  missionStore.chooseMission(todayMission.value.id)
  router.push('/plan')
}
</script>

<style scoped>
.mission-card {
  margin-top: 18px;
  border: 1px solid var(--line-2);
  border-radius: 14px;
  padding: 16px;
}

.mission-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.mission-title { font-size: 15px; font-weight: 500; }
.mission-meta { font-size: 11.5px; color: var(--ink-3); margin-top: 4px; }

.start-btn { width: 100%; margin-top: 16px; }

.week-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-value { font-size: 22px; font-weight: 600; color: var(--green-dark); }
.stat-label { font-size: 11px; color: var(--ink-3); margin-top: 2px; }

.link-btn {
  background: none;
  border: none;
  color: var(--green-dark);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
}
</style>
