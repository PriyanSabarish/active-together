<template>
  <AppHeader />
  <div class="scroll-area" :class="{ centred: neverUsed }">
    <!-- Gap 3 — never used, as opposed to one quiet day inside a real week. -->
    <template v-if="neverUsed">
      <span class="empty-glyph">–</span>
      <h1>No activity yet</h1>
      <p class="subtitle">Once Daniel finishes his first mission, you'll see patterns here — by day and activity type.</p>
      <button class="btn btn-primary cta" @click="router.push('/play')">Find a mission <span class="btn-arrow">→</span></button>
    </template>

    <template v-else>
    <h1>This week</h1>

    <div class="stat-grid">
      <div class="stat-tile primary">
        <p class="stat-num">{{ historyStore.thisWeekCount }}</p>
        <p class="stat-sub">{{ historyStore.thisWeekCount === 1 ? 'outing' : 'outings' }} this week</p>
      </div>
      <div class="stat-tile">
        <p class="stat-num">{{ historyStore.lastWeekCount }}</p>
        <p class="stat-sub">last week</p>
      </div>
    </div>

    <div class="row-list log">
      <button
        v-for="day in weekDays"
        :key="day.date"
        class="row as-btn"
        :class="{ empty: !day.record }"
        :disabled="!day.record"
        @click="router.push(`/week/${day.date}`)"
      >
        <span class="row-key">{{ day.label }}</span>
        <span class="row-main">
          <template v-if="day.record">{{ day.record.missionTitle }} · {{ day.record.placeName }}</template>
          <template v-else>No activity logged</template>
        </span>
        <span v-if="day.record" class="row-end">{{ day.record.durationMin }} min</span>
      </button>
    </div>

    <p class="quiet-note">No targets, no streaks, no score. Just what you did.</p>

    <h2 class="sect">Activity mix</h2>
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
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useHistoryStore, mondayOf } from '../historyStore'
import { categoryLabel } from '../store'

const router = useRouter()
const historyStore = useHistoryStore()

const neverUsed = computed(() => historyStore.records.length === 0)

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

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
h1 { margin-bottom: 18px; }

.centred {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 28px;
}

.centred h1 { margin-bottom: 6px; }

.empty-glyph {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--tint);
  color: var(--ink-4);
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.cta { width: 100%; margin-top: 22px; }

.log { margin-top: 18px; border-top: 1px solid var(--line-2); }

.as-btn {
  width: 100%;
  background: none;
  border: none;
  font-family: inherit;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}

.as-btn:disabled { cursor: default; }
.row.empty .row-main { color: var(--ink-4); }
.row.empty .row-key { color: var(--ink-5); }

.quiet-note { margin-top: 16px; font-size: 13px; color: var(--ink-4); line-height: 1.5; }

.sect { margin-top: 26px; }

.mix-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  margin-top: 12px;
  background: var(--tint);
}

.mix-legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 10px; }

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: var(--ink-3);
}

.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.body-text { font-size: 13px; color: var(--ink-4); margin-top: 10px; }
</style>
