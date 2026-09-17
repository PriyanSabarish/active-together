<template>
  <AppHeader />

  <div class="scroll-area">
    <button class="pill crumb" @click="router.push('/week')">‹ This week</button>
    <h1 class="day-name" style="margin-top: 14px">{{ dayName }}</h1>

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
          <p class="eyebrow-accent" style="margin-top: 16px">Daniel's feedback</p>
          <div class="note-card">"{{ feedbackQuote(r.feedback) }}" — picked after finishing the mission, shown here for context, not scored.</div>
        </template>

        <p class="eyebrow-accent" style="margin-top: 16px">Record details</p>
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
// One day's records from the Week log, with the child's feedback quoted for
// context (never scored). Records can be deleted here; editing is not wired.

import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useHistoryStore, feedbackLabel, feedbackQuote } from '../historyStore'
import { categoryLabel } from '../store'

const props = defineProps({ date: { type: String, required: true } })
const router = useRouter()
const historyStore = useHistoryStore()

const records = computed(() => historyStore.byDate[props.date] ?? [])
const dayName = computed(() => new Date(props.date).toLocaleDateString('en-AU', { weekday: 'long' }))
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

.day-name { color: var(--ink); }

.record-block { margin-top: 4px; }
.record-block + .record-block { margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--line); }

.record-card {
  margin-top: 16px;
  border-radius: var(--radius-card);
  background: var(--card);
  box-shadow: var(--shadow-card);
  padding: 16px;
}

.place-name { font-size: 14.5px; font-weight: 600; }
.place-meta { font-size: 11.5px; color: var(--ink-3); margin-top: 2px; }

.record-line { font-size: 12px; color: var(--ink-2); margin-top: 10px; line-height: 1.5; }

.record-feedback { margin-top: 12px; }

.btn-row .danger-btn { color: var(--danger); box-shadow: inset 0 0 0 1.5px rgba(178, 58, 46, 0.35); }
</style>
