<template>
  <div class="app-bar">
    <button class="back-btn" aria-label="Back to this week" @click="router.push('/insights')">
      <svg width="18" height="24" viewBox="0 0 18 24">
        <path d="M13 4 L5 12 L13 20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
    <span class="page-title">Back to this week</span>
    <span class="spacer" />
  </div>

  <div class="scroll-area">
    <h1 class="day-name">{{ dayName }}</h1>

    <template v-if="records.length">
      <p class="subtitle">{{ records.length === 1 ? 'One activity logged automatically' : `${records.length} activities logged automatically` }}</p>

      <div v-for="r in records" :key="r.id" class="record-block">
        <div class="record-card">
          <p class="place-name">{{ r.placeName }}</p>
          <p class="place-meta">{{ categoryLabel(r.category) }}</p>
          <p class="record-line">Mission: {{ r.missionTitle }}</p>
          <p class="record-line">
            Duration: {{ r.durationMin }} min · {{ r.photoStepsCount }} of {{ r.totalSteps }} steps confirmed by photo · logged automatically at {{ r.time }}
          </p>
          <span v-if="r.feedback" class="badge good record-feedback">{{ feedbackLabel(r.feedback) }}</span>
        </div>

        <template v-if="r.feedback">
          <p class="section-eyebrow" style="margin-top: 16px">Daniel's feedback</p>
          <div class="note-card">"{{ feedbackQuote(r.feedback) }}" — picked after finishing the mission, shown here for context, not scored.</div>
        </template>

        <p class="section-eyebrow" style="margin-top: 16px">Record details</p>
        <div class="note-card">This record was written automatically when the mission completed. No manual entry was made. You can edit or delete this record below.</div>

        <div class="btn-row" style="margin-top: 16px">
          <button class="btn btn-secondary" disabled title="Editing isn't wired up yet">Edit record</button>
          <button class="btn btn-secondary danger-btn" @click="historyStore.removeRecord(r.id)">Delete record</button>
        </div>
      </div>
    </template>

    <template v-else>
      <p class="subtitle">Nothing was logged on this day.</p>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useHistoryStore, feedbackLabel, feedbackQuote } from '../historyStore'
import { categoryLabel } from '../store'

const props = defineProps({ date: { type: String, required: true } })
const router = useRouter()
const historyStore = useHistoryStore()

const records = computed(() => historyStore.byDate[props.date] ?? [])
const dayName = computed(() => new Date(props.date).toLocaleDateString(undefined, { weekday: 'long' }))
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

.day-name { color: var(--green-dark); }

.record-block { margin-top: 4px; }
.record-block + .record-block { margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--line); }

.record-card {
  margin-top: 16px;
  border-radius: 12px;
  background: var(--paper);
  padding: 16px;
}

.place-name { font-size: 14.5px; font-weight: 500; }
.place-meta { font-size: 11.5px; color: var(--ink-3); margin-top: 2px; }

.record-line { font-size: 12px; color: var(--ink-2); margin-top: 10px; line-height: 1.5; }

.record-feedback { margin-top: 12px; }

.btn-row .danger-btn { color: #B23A2E; border-color: #E3B7AF; }
</style>
