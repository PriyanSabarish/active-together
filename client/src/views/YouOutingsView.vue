<template>
  <AppHeader />
  <div class="scroll-area">
    <SubPageHead title="Your outings" />

    <!-- The child's own collection (story 10.1): no totals to reach, nothing locked. -->
    <div class="strip">
      <button
        v-for="t in tiles"
        :key="t.key"
        class="tile"
        :class="{ on: expand === t.key, tappable: t.tappable && t.n > 0 }"
        :disabled="!(t.tappable && t.n > 0)"
        @click="expand = expand === t.key ? null : t.key"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="t.d" /></svg>
        <span class="tile-n">{{ t.n }}</span>
        <span class="tile-label">{{ t.label }}</span>
      </button>
    </div>

    <div v-if="expandItems.length" class="expand">
      <div v-for="x in expandItems" :key="x.name" class="x-item">
        <span class="x-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path :d="x.d" /></svg>
        </span>
        <span class="x-name">{{ x.name }}</span>
      </div>
    </div>

    <template v-if="months.length">
      <div v-for="m in months" :key="m.name">
        <p class="month">{{ m.name }}</p>
        <div class="grid">
          <button v-for="p in m.photos" :key="p.photo.id" class="cell" :style="tileStyle(p.photo)" :title="p.label" :aria-label="p.label" @click="router.push(`/week/entry/${p.recordId}`)" />
        </div>
      </div>
      <p class="note">Photos stay on this phone. Clearing your browser data removes them.</p>
    </template>

    <div v-else class="empty">
      <span class="empty-art">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8.5A2 2 0 0 1 6 6.5h2l1.5-2h5l1.5 2h2a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z M12 16.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" /></svg>
      </span>
      <p class="empty-text">{{ historyStore.records.length ? "Take a photo at the end of a mission and it'll show up here." : 'Photos from your outings will show up here.' }}</p>
    </div>
  </div>
</template>

<script setup>
// You → Your outings: places explored, kinds of play tried and the weekly
// streak (stories 10.1 / 10.2), then every outing photo grouped by month,
// newest first (10.4). A tile with something in it opens its icons; a photo
// opens its outing. A broken streak just shows a smaller number, no message.

import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import SubPageHead from '../components/SubPageHead.vue'
import { useHistoryStore, weekStreak } from '../historyStore'
import { categoryLabel } from '../store'
import { usePhotosFor, tileStyle } from '../journal'
import { categoryIcon, PIN, SHAPES, CALENDAR } from '../taskIcons'

const router = useRouter()
const historyStore = useHistoryStore()
const photosFor = usePhotosFor()
const expand = ref(null)

const places = computed(() => {
  const seen = new Map()
  for (const r of historyStore.records) {
    if (r.placeName === 'Home' || seen.has(r.placeName)) continue
    seen.set(r.placeName, { name: r.placeName.replace(/ (Park|Reserve|Gardens?)( North| South)?$/, ''), d: categoryIcon(r.category) })
  }
  return [...seen.values()]
})

const kinds = computed(() => {
  const seen = new Map()
  for (const r of historyStore.records) {
    if (!seen.has(r.category)) seen.set(r.category, { name: r.category === 'home' ? 'At home' : categoryLabel(r.category), d: categoryIcon(r.category) })
  }
  return [...seen.values()]
})

const streak = computed(() => weekStreak(historyStore.records))

const tiles = computed(() => [
  { key: 'places', d: PIN, n: places.value.length, label: places.value.length === 1 ? 'place' : 'places', tappable: true },
  { key: 'play', d: SHAPES, n: kinds.value.length, label: 'kinds of play', tappable: true },
  { key: 'streak', d: CALENDAR, n: streak.value, label: streak.value === 1 ? 'week' : 'weeks in a row', tappable: false }
])

const expandItems = computed(() => (expand.value === 'places' ? places.value : expand.value === 'play' ? kinds.value : []))

const thisYear = new Date().getFullYear()
const months = computed(() => {
  const out = []
  const recs = [...historyStore.records].sort((a, b) => b.date.localeCompare(a.date))
  for (const r of recs) {
    const d = new Date(r.date)
    const name = d.toLocaleDateString('en-AU', d.getFullYear() === thisYear ? { month: 'long' } : { month: 'long', year: 'numeric' })
    for (const photo of photosFor(r)) {
      let m = out.find((x) => x.name === name)
      if (!m) out.push((m = { name, photos: [] }))
      m.photos.push({ photo, recordId: r.id, label: `${r.missionTitle} · ${r.placeName}` })
    }
  }
  return out
})
</script>

<style scoped>
.strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }

.tile {
  padding: 13px 12px 12px;
  border: none;
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow-card);
  font-family: inherit;
  text-align: left;
  color: var(--green);
  display: flex;
  flex-direction: column;
  cursor: default;
  transition: box-shadow 0.18s ease;
}

.tile.tappable { cursor: pointer; }
.tile.on { box-shadow: inset 0 0 0 1.5px var(--green), var(--shadow-card); }
.tile-n { margin-top: 8px; font-family: var(--font-display); font-weight: 700; font-size: 28px; line-height: 1; color: var(--ink); }
.tile-label { margin-top: 4px; font-size: 12px; line-height: 1.25; color: rgba(30, 42, 31, 0.55); }

.expand {
  margin-top: 8px;
  padding: 16px 10px 14px;
  border-radius: 16px;
  background: var(--card);
  box-shadow: var(--shadow-card);
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px 4px;
}

.x-item { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.x-icon { width: 58px; height: 58px; border-radius: 50%; background: rgba(47, 107, 54, 0.12); color: var(--green); display: flex; align-items: center; justify-content: center; }
.x-name { font-size: 11.5px; font-weight: 600; color: rgba(30, 42, 31, 0.55); text-align: center; }

.month { font-size: 11px; font-weight: 600; letter-spacing: 1.6px; text-transform: uppercase; color: var(--ink-4); margin: 22px 0 10px; }
.grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
.cell { aspect-ratio: 1 / 1; border: none; border-radius: 12px; cursor: pointer; }
.cell:active { transform: scale(0.97); }

.note { margin: 22px 4px 18px; font-size: 12.5px; line-height: 1.5; color: var(--ink-4); text-align: center; text-wrap: pretty; }

.empty { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 56px 20px 0; }
.empty-art { width: 96px; height: 96px; border-radius: 50%; background: rgba(47, 107, 54, 0.1); color: var(--green); display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
.empty-text { max-width: 260px; font-family: var(--font-display); font-weight: 600; font-size: 17px; line-height: 1.3; letter-spacing: -0.3px; text-wrap: pretty; }
</style>
