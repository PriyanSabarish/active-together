<template>
  <AppHeader />
  <div ref="listEl" class="scroll-area diary">
    <div class="title-row">
      <h1>Activity diary</h1>
      <button v-if="offset < 0" class="jump" @click="go(0)">This week</button>
    </div>

    <div class="week-nav">
      <button class="nav-btn" aria-label="Previous week" :disabled="offset <= minOffset" @click="go(offset - 1)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7" /></svg>
      </button>
      <span class="range">{{ rangeLabel }}</span>
      <button class="nav-btn" aria-label="Next week" :disabled="offset >= 0" @click="go(offset + 1)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
      </button>
    </div>

    <!-- Mon-Sun strip: a filled day jumps to its group. Swipe to change week. -->
    <div class="days" @pointerdown="swipeStart" @pointerup="swipeEnd">
      <button v-for="d in days" :key="d.iso" class="day" :class="{ has: d.items.length, today: d.today, future: d.future }" :disabled="!d.items.length" @click="jumpDay(d)">
        <span class="day-box">
          <svg v-for="(it, i) in d.items" :key="i" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="kindIcon(it)" /></svg>
        </span>
        <span class="day-name">{{ d.name }}</span>
      </button>
    </div>

    <div v-if="weekRecords.length" class="mix">
      <span v-for="k in mix" :key="k.id" class="mix-item">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="k.d" /></svg>
        <b>{{ k.n }}</b>{{ k.label }}
      </span>
      <span class="mix-mins">{{ totalMins }} min</span>
    </div>
    <p v-else class="empty">No outings this week.</p>

    <div v-for="g in groups" :key="g.iso" :data-day="g.iso" class="group" :class="{ flash: flash === g.iso }">
      <p class="group-label">{{ g.label }}</p>
      <button v-for="r in g.items" :key="r.id" class="entry" @click="router.push(`/week/entry/${r.id}`)">
        <span class="tile" :style="cover(r)">
          <svg v-if="!photosFor(r).length" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(r.category)" /></svg>
          <span v-if="photosFor(r).length > 1" class="count">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path :d="CAMERA" /></svg>{{ photosFor(r).length }}
          </span>
        </span>
        <span class="entry-text">
          <span class="entry-title">{{ r.missionTitle }}</span>
          <span class="entry-sub">
            {{ r.placeName }} · {{ r.durationMin }} min
            <template v-if="r.feedback">
              <span>·</span>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="FEEDBACK_ICON[r.feedback]" /></svg>
              {{ feedbackLabel(r.feedback) }}
            </template>
          </span>
        </span>
      </button>
    </div>

    <p class="quiet-note">No targets, no score. Just what you did.</p>
  </div>
</template>

<script setup>
// Week tab: the Activity diary (Canvas → WeekTab). One Monday-Sunday week at
// a time (Melbourne local time), stepped with the arrows or a swipe. The day
// strip shows an icon per outing; the list below groups outings by day, newest
// day first, each with a photo thumbnail (count when more than one) and the
// child's feedback. A tap opens the outing. All data is device-local.

import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useHistoryStore, mondayOf, kindOf, KINDS, feedbackLabel, localIso } from '../historyStore'
import { categoryIcon, CAMERA, FEEDBACK_ICON, TREE, STAR, HOUSE } from '../taskIcons'
import { usePhotosFor, tileStyle } from '../journal'

const router = useRouter()
const historyStore = useHistoryStore()
const photosFor = usePhotosFor()

const KIND_ICON = { park: TREE, exploring: STAR, home: HOUSE }
const kindIcon = (r) => KIND_ICON[kindOf(r)]

const WD = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const offset = ref(0) // 0 = this week, -1 = last week, ...
const flash = ref(null)
const listEl = ref(null)

const iso = localIso
const todayIso = iso(new Date())

// Earliest week with a record, so the arrows stop where the diary starts.
const minOffset = computed(() => {
  if (!historyStore.records.length) return 0
  const first = Math.min(...historyStore.records.map((r) => mondayOf(new Date(r.date)).getTime()))
  return Math.min(0, Math.round((first - mondayOf(new Date()).getTime()) / (7 * 86400000)))
})

const weekStart = computed(() => {
  const d = mondayOf(new Date())
  d.setDate(d.getDate() + offset.value * 7)
  return d
})

const rangeLabel = computed(() => {
  const end = new Date(weekStart.value)
  end.setDate(end.getDate() + 6)
  const fmt = (d, month) => d.toLocaleDateString('en-AU', month ? { day: 'numeric', month: 'short' } : { day: 'numeric' })
  const sameMonth = end.getMonth() === weekStart.value.getMonth()
  return `${fmt(weekStart.value, !sameMonth)} – ${fmt(end, true)}`
})

const days = computed(() => WD.map((name, i) => {
  const d = new Date(weekStart.value)
  d.setDate(d.getDate() + i)
  const dayIso = iso(d)
  return {
    name,
    full: DAY_FULL[i],
    iso: dayIso,
    items: (historyStore.byDate[dayIso] ?? []),
    today: dayIso === todayIso,
    future: dayIso > todayIso
  }
}))

const weekRecords = computed(() => days.value.flatMap((d) => d.items))
const totalMins = computed(() => weekRecords.value.reduce((a, r) => a + (r.durationMin || 0), 0))
const mix = computed(() => KINDS
  .map((k) => ({ ...k, d: KIND_ICON[k.id], n: weekRecords.value.filter((r) => kindOf(r) === k.id).length }))
  .filter((k) => k.n))

const groups = computed(() => days.value
  .filter((d) => d.items.length)
  .reverse()
  .map((d) => ({ iso: d.iso, label: (d.today ? 'Today · ' : '') + d.full, items: d.items })))

const cover = (r) => {
  const p = photosFor(r)[0]
  return p ? tileStyle(p) : {}
}

function go(n) {
  if (n < minOffset.value || n > 0 || n === offset.value) return
  offset.value = n
  flash.value = null
  if (listEl.value) listEl.value.scrollTop = 0
}

async function jumpDay(d) {
  await nextTick()
  const box = listEl.value
  const el = box?.querySelector(`[data-day="${d.iso}"]`)
  if (!el) return
  box.scrollTo?.({ top: el.offsetTop - box.offsetTop - 8, behavior: 'smooth' })
  flash.value = d.iso
  setTimeout(() => { if (flash.value === d.iso) flash.value = null }, 900)
}

let startX = null
function swipeStart(e) { startX = e.clientX }
function swipeEnd(e) {
  if (startX == null) return
  const dx = e.clientX - startX
  startX = null
  if (Math.abs(dx) > 40) go(offset.value + (dx < 0 ? 1 : -1))
}
</script>

<style scoped>
.diary { position: relative; }

.title-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 4px 0 2px; }
.title-row h1 { margin: 0; font-size: 29px; letter-spacing: -0.8px; }
.jump { height: 44px; padding: 0 10px; margin-right: -10px; background: none; border: none; font-family: inherit; font-size: 13.5px; font-weight: 600; color: var(--green); cursor: pointer; }

.week-nav { display: flex; align-items: center; margin: 0 -12px; }
.nav-btn { width: 44px; height: 44px; flex: none; display: flex; align-items: center; justify-content: center; border: none; border-radius: 999px; background: none; color: var(--ink); cursor: pointer; }
.nav-btn:active { background: var(--tint); }
.nav-btn:disabled { opacity: 0.25; cursor: default; background: none; }
.range { flex: 1; text-align: center; font-size: 14px; font-weight: 600; }

.days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 5px;
  padding: 4px 0;
  margin: 4px 0 10px;
  touch-action: pan-y;
  user-select: none;
}

.day { display: flex; flex-direction: column; align-items: center; gap: 5px; background: none; border: none; font-family: inherit; padding: 0; cursor: pointer; }
.day:disabled { cursor: default; }

.day-box {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: rgba(30, 42, 31, 0.05);
  color: var(--paper);
}

.day.has .day-box { background: var(--green); }
.day.future .day-box { background: transparent; box-shadow: inset 0 0 0 1.5px rgba(30, 42, 31, 0.12); }
.day.today .day-box { box-shadow: 0 0 0 2px var(--paper), 0 0 0 4px var(--accent); }
.day.has:active .day-box { transform: scale(0.95); }
.day-name { font-size: 11px; font-weight: 600; color: var(--ink-3); }
.day.today .day-name { color: var(--accent); }

.mix {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px 2px;
  border-top: 1px solid rgba(30, 42, 31, 0.1);
  margin-bottom: 10px;
}

.mix-item { display: flex; align-items: center; gap: 5px; font-size: 13.5px; color: rgba(30, 42, 31, 0.65); }
.mix-item svg { color: var(--green); }
.mix-item b { font-weight: 700; color: var(--ink); }
.mix-mins { margin-left: auto; font-size: 13px; color: var(--ink-4); }

.empty { padding: 14px 2px; border-top: 1px solid rgba(30, 42, 31, 0.1); font-size: 14px; color: rgba(30, 42, 31, 0.5); }

.group { margin-bottom: 6px; border-radius: 12px; transition: background 0.4s ease; }
.group.flash { background: rgba(232, 145, 58, 0.14); }
.group-label { font-size: 12px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--accent); padding: 4px 0 6px; }

.entry {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border: none;
  border-top: 1px solid rgba(30, 42, 31, 0.1);
  background: none;
  font-family: inherit;
  text-align: left;
  color: var(--ink);
  cursor: pointer;
}

.entry:active { background: rgba(30, 42, 31, 0.03); }

.tile {
  position: relative;
  width: 48px;
  height: 48px;
  flex: none;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(47, 107, 54, 0.1);
  color: var(--green);
}

.count {
  position: absolute;
  right: -5px;
  bottom: -5px;
  display: flex;
  align-items: center;
  gap: 3px;
  height: 20px;
  padding: 0 6px 0 5px;
  border-radius: 999px;
  background: var(--ink);
  box-shadow: 0 0 0 2px var(--paper);
  font-size: 11px;
  font-weight: 700;
  color: var(--paper);
}

.entry-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.entry-title { font-size: 15px; font-weight: 600; }
.entry-sub { margin-top: 2px; display: flex; align-items: center; gap: 5px; font-size: 13px; color: rgba(30, 42, 31, 0.55); flex-wrap: wrap; }
.entry-sub svg { color: rgba(30, 42, 31, 0.6); }

.quiet-note { margin: 18px 0 4px; font-size: 12.5px; color: var(--ink-4); text-align: center; }
</style>
