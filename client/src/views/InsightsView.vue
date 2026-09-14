<template>
  <AppHeader plain />
  <div class="scroll-area">
    <p class="section-eyebrow">Insights</p>
    <h1>This week</h1>
    <p class="subtitle">Patterns over time — no scores, no targets.</p>

    <div class="week-card">
      <div class="week-row">
        <span class="week-label">Last week</span>
        <div class="week-bar"><span class="bar-fill muted" :style="{ width: lastWeekBarPct + '%' }" /></div>
        <span class="week-count muted">{{ historyStore.lastWeekCount }}</span>
      </div>
      <div class="week-row">
        <span class="week-label">This week</span>
        <div class="week-bar"><span class="bar-fill" :style="{ width: thisWeekBarPct + '%' }" /></div>
        <span class="week-count">{{ historyStore.thisWeekCount }}</span>
      </div>
      <p class="week-note">Counts only, no percentage — a decrease is shown the same way.</p>
    </div>

    <p class="section-eyebrow" style="margin-top: 24px">By day</p>
    <button
      v-for="day in weekDays"
      :key="day.date"
      class="day-row"
      :class="{ empty: !day.record }"
      :disabled="!day.record"
      @click="router.push(`/insights/${day.date}`)"
    >
      <span class="day-abbr">{{ day.label }}</span>
      <span class="day-info">
        <template v-if="day.record">{{ day.record.placeName }} · {{ day.record.durationMin }} min</template>
        <template v-else>No activity logged</template>
      </span>
      <span v-if="day.record" class="day-emoji">{{ feedbackEmoji(day.record.feedback) || '—' }}</span>
    </button>

    <p class="section-eyebrow" style="margin-top: 24px">Activity mix</p>
    <template v-if="mix.length">
      <div class="mix-bar">
        <span v-for="seg in mix" :key="seg.category" :style="{ width: seg.pct + '%', background: seg.color }" />
      </div>
      <div class="mix-legend">
        <span v-for="seg in mix" :key="seg.category" class="legend-item">
          <span class="dot" :style="{ background: seg.color }" />
          {{ categoryLabel(seg.category) }}
        </span>
      </div>
    </template>
    <p v-else class="body-text">No activity logged this week yet.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useHistoryStore, mondayOf, feedbackEmoji } from '../historyStore'
import { categoryLabel } from '../store'

const router = useRouter()
const historyStore = useHistoryStore()

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

function isoDate(d) {
  return d.toISOString().slice(0, 10)
}

const weekDays = computed(() => {
  const monday = mondayOf(new Date())
  return DAY_LABELS.map((label, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    const date = isoDate(d)
    const records = historyStore.byDate[date] ?? []
    return { date, label, record: records[0] ?? null }
  })
})

const maxWeekCount = computed(() => Math.max(historyStore.thisWeekCount, historyStore.lastWeekCount, 1))
const thisWeekBarPct = computed(() => (historyStore.thisWeekCount / maxWeekCount.value) * 100)
const lastWeekBarPct = computed(() => (historyStore.lastWeekCount / maxWeekCount.value) * 100)

// Reuses store.js's CATEGORY_META keys; only a subset shows up in the mock
// data, but every category gets a distinct swatch.
const CATEGORY_COLOR = {
  playground: 'var(--green)',
  park_and_garden: 'var(--green-dark)',
  picnic_day_use: 'var(--amber)',
  sports_ground: 'var(--green-mid)',
  court: 'var(--ink-3)',
  skate_bmx: 'var(--ink-4)',
  trail_access: 'var(--orange)'
}

const mix = computed(() => {
  const rows = historyStore.categoryMixThisWeek
  const total = rows.reduce((s, c) => s + c.count, 0)
  if (!total) return []
  return rows.map((c) => ({
    category: c.category,
    pct: (c.count / total) * 100,
    color: CATEGORY_COLOR[c.category] ?? 'var(--ink-4)'
  }))
})
</script>

<style scoped>
.week-card {
  margin-top: 18px;
  border-radius: 12px;
  background: var(--paper);
  padding: 16px 18px;
}

.week-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.week-row + .week-row { margin-top: 12px; }

.week-label { width: 68px; font-size: 12px; color: var(--ink-3); flex-shrink: 0; }

.week-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: var(--line-2);
  overflow: hidden;
}

.bar-fill { display: block; height: 100%; background: var(--green); border-radius: 4px; }
.bar-fill.muted { background: var(--ink-5); }

.week-count { width: 20px; text-align: right; font-size: 13px; font-weight: 600; }
.week-count.muted { color: var(--ink-4); font-weight: 500; }

.week-note {
  margin-top: 12px;
  font-size: 10.5px;
  color: var(--ink-4);
  line-height: 1.4;
}

.day-row {
  width: 100%;
  height: 48px;
  margin-top: 8px;
  border: none;
  border-radius: 10px;
  background: var(--paper);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  font-family: inherit;
  cursor: pointer;
}

.day-row:disabled { cursor: default; }
.day-row.empty .day-info { color: var(--ink-4); }

.day-abbr { width: 32px; font-size: 12.5px; font-weight: 600; flex-shrink: 0; }
.day-info { flex: 1; text-align: left; font-size: 12.5px; }
.day-emoji { font-size: 15px; }

.mix-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  margin-top: 4px;
}

.mix-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 10px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--ink-3);
}

.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.body-text { font-size: 12px; color: var(--ink-4); margin-top: 8px; }
</style>
