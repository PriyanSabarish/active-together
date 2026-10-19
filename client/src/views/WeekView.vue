<template>
  <AppHeader />
  <div ref="listEl" class="scroll-area diary">
    <h1>Activity diary</h1>

    <div class="cur-row">
      <span class="cur-tag" :class="{ now: offset === 0 }">{{ weekLabel(offset) }}</span>
      <span class="cur-range">{{ rangeLabel(offset) }}</span>
      <button v-if="offset < 0" class="jump" @click="scrollToPage(0)">This week</button>
    </div>

    <!-- One page per Monday-Sunday week, newest first; swipe left for older weeks. -->
    <div ref="pagerEl" class="pager" @scroll.passive="onScroll">
      <div v-for="p in pages" :key="p.offset" class="page">
        <div class="card week-days">
          <button v-for="d in p.days" :key="d.iso" class="wd" :disabled="!d.items.length || p.offset !== offset" @click="jumpDay(d)">
            <span class="wd-letter" :class="{ today: d.today }">{{ d.letter }}</span>
            <span class="wd-date" :class="{ today: d.today, has: d.items.length, future: d.future }">{{ d.date }}</span>
            <span class="wd-icons">
              <svg v-for="(it, i) in d.items.slice(0, 2)" :key="i" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path :d="kindIcon(it)" /></svg>
            </span>
          </button>
        </div>

        <div class="card stats">
          <div class="mins-row"><span class="mins">{{ p.mins }}</span><span class="mins-unit">min active</span></div>
          <p v-if="p.delta" class="delta" :class="p.delta.dir">{{ p.delta.text }}</p>
          <div class="curve" :style="{ height: CURVE_H + 'px' }">
            <span v-for="g in GRID" :key="g.m" class="grid" :class="{ dashed: g.m === 30 }" :style="{ top: yOf(g.m) + 'px' }" />
            <span v-for="g in GRID" :key="'l' + g.m" class="grid-label" :style="{ top: yOf(g.m) - 7 + 'px' }">{{ g.m }}</span>
            <svg width="100%" :height="CURVE_H" :viewBox="`0 0 700 ${CURVE_H}`" preserveAspectRatio="none" aria-hidden="true">
              <path :d="p.area" fill="rgba(47,107,54,.1)" />
              <path :d="p.curve" fill="none" stroke="#2F6B36" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <template v-for="pt in p.pts" :key="pt.iso">
              <span class="pt" :class="{ on: pt.min, today: pt.today, miss: pt.miss }" :style="{ left: pt.left, top: pt.y + 'px' }" />
              <span v-if="pt.min || pt.miss" class="pt-label" :style="{ left: pt.left, top: pt.y - 26 + 'px' }">{{ pt.min }}′</span>
            </template>
          </div>
          <div class="guilt"><span class="guilt-big">{{ p.guiltBig }}</span><span class="guilt-line">{{ p.guiltLine }}</span></div>
        </div>
      </div>
    </div>

    <div v-if="pages.length > 1" class="dots">
      <span v-for="d in dots" :key="d.offset" class="dot" :class="{ on: d.offset === offset }" @click="scrollToPage(-d.offset)" />
    </div>

    <div v-if="!groups.length" class="card empty">
      <p class="empty-title">No outings this week</p>
      <p class="empty-sub">Swipe to another week, or plan one from Start.</p>
    </div>

    <div v-for="g in groups" :key="g.iso" :data-day="g.iso" class="group" :class="{ flash: flash === g.iso }">
      <p class="group-label">
        {{ g.full }} · {{ g.date }}
        <span v-if="g.today" class="today-pill">Today</span>
      </p>
      <div class="entries">
        <button v-for="r in g.items" :key="r.id" class="entry" @click="router.push(`/week/entry/${r.id}`)">
          <span v-if="photosFor(r).length" class="photo" :style="cover(r)">
            <span class="kind-pill">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="kindIcon(r)" /></svg>
              {{ kindLabel(r) }}
            </span>
            <span class="photo-count">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path :d="CAMERA" /></svg>{{ photosFor(r).length }}
            </span>
          </span>
          <span class="entry-row">
            <span v-if="!photosFor(r).length" class="icon-tile">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(r.category)" /></svg>
            </span>
            <span class="entry-text">
              <span class="entry-title">{{ r.missionTitle }}</span>
              <span class="entry-sub">{{ r.placeName }} · {{ r.durationMin }} min</span>
            </span>
            <span v-if="r.feedback" class="fb" :class="{ fun: r.feedback === 'fun' }">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="FEEDBACK_ICON[r.feedback]" /></svg>
              {{ feedbackLabel(r.feedback) }}
            </span>
          </span>
        </button>
      </div>
    </div>

    <p class="quiet-note">No targets, no score. Just what you did.</p>
  </div>
</template>

<script setup>
// Week tab: the Activity diary (Week Tab design, variant P). A swipeable pager
// of Monday-Sunday weeks (Melbourne local time), newest first. Each page has a
// day card (date + outing icons) and a stats card (minutes, change on last
// week, smooth per-day curve). The journal below lists the outings of the week
// on screen, newest day first. Days with no outing get an orange point and are
// counted under the curve, as in the design. All data is device-local.

import { computed, nextTick, onMounted, ref } from 'vue'
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
const kindLabel = (r) => KINDS.find((k) => k.id === kindOf(r))?.label ?? ''

const LETTERS = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
const DAY_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

// Curve geometry: minutes are drawn on a fixed 0-60 scale.
const CURVE_H = 124
const CURVE_TOP = 18
const SCALE = (CURVE_H - 12 - CURVE_TOP) / 60
const yOf = (m) => CURVE_H - 12 - Math.min(60, m) * SCALE
const GRID = [{ m: 60 }, { m: 30 }, { m: 0 }]

const offset = ref(0) // 0 = this week, -1 = last week, ...
const flash = ref(null)
const listEl = ref(null)
const pagerEl = ref(null)

const iso = localIso
const todayIso = iso(new Date())

// Earliest week with a record, so the pager stops where the diary starts.
const minOffset = computed(() => {
  if (!historyStore.records.length) return 0
  const first = Math.min(...historyStore.records.map((r) => mondayOf(new Date(r.date)).getTime()))
  return Math.min(0, Math.round((first - mondayOf(new Date()).getTime()) / (7 * 86400000)))
})

const weekStartOf = (off) => {
  const d = mondayOf(new Date())
  d.setDate(d.getDate() + off * 7)
  return d
}

const rangeLabel = (off) => {
  const start = weekStartOf(off)
  const end = new Date(start)
  end.setDate(end.getDate() + 6)
  const fmt = (d, month) => d.toLocaleDateString('en-AU', month ? { day: 'numeric', month: 'short' } : { day: 'numeric' })
  return `${fmt(start, start.getMonth() !== end.getMonth())} – ${fmt(end, true)}`
}

const weekLabel = (off) => (off === 0 ? 'This week' : off === -1 ? 'Last week' : `${-off} weeks ago`)

const daysOf = (off) => {
  const start = weekStartOf(off)
  return LETTERS.map((letter, i) => {
    const d = new Date(start)
    d.setDate(d.getDate() + i)
    const dayIso = iso(d)
    return {
      letter,
      full: DAY_FULL[i],
      iso: dayIso,
      date: d.getDate(),
      items: historyStore.byDate[dayIso] ?? [],
      today: dayIso === todayIso,
      future: dayIso > todayIso
    }
  })
}

const sumMins = (items) => items.reduce((a, r) => a + (r.durationMin || 0), 0)

// Smooth curve through one point per day (x = column centre of a 700-wide box).
function curvePath(ys) {
  const xs = ys.map((_, n) => 50 + n * 100)
  let c = `M${xs[0]} ${ys[0]}`
  for (let n = 1; n < ys.length; n++) {
    const mx = (xs[n - 1] + xs[n]) / 2
    c += ` C${mx} ${ys[n - 1]} ${mx} ${ys[n]} ${xs[n]} ${ys[n]}`
  }
  return c
}

// Newest week first, down to the earliest week with a record.
const pages = computed(() => {
  const out = []
  for (let off = 0; off >= minOffset.value; off--) {
    const days = daysOf(off)
    const mins = days.map((d) => sumMins(d.items))
    const total = mins.reduce((a, b) => a + b, 0)
    const ys = mins.map((m) => yOf(m))
    const curve = curvePath(ys)
    let delta = null
    if (off === minOffset.value) {
      delta = { dir: 'flat', text: 'Your first week' }
    } else {
      const diff = total - sumMins(daysOf(off - 1).flatMap((d) => d.items))
      delta = diff > 0 ? { dir: 'up', text: `↑ ${diff} min on last week` }
        : diff < 0 ? { dir: 'down', text: `↓ ${-diff} min on last week` }
          : { dir: 'flat', text: 'Same as last week' }
    }
    const ti = days.findIndex((d) => d.today)
    const past = (n) => off < 0 || (ti >= 0 && n <= ti)
    const zeros = mins.filter((m, n) => !m && past(n)).length
    out.push({
      offset: off,
      guiltBig: zeros + (zeros === 1 ? ' day' : ' days'),
      guiltLine: zeros ? 'with no activity at all. Plan an outing this weekend?' : 'with no activity. On a roll.',
      days,
      mins: total,
      delta,
      curve,
      area: `${curve} L650 ${CURVE_H} L50 ${CURVE_H} Z`,
      pts: days.map((d, n) => ({ iso: d.iso, min: mins[n], y: ys[n], left: `${((n + 0.5) / 7) * 100}%`, today: d.today, miss: !mins[n] && past(n) }))
    })
  }
  return out
})

// A window of dots so a long diary does not run off the screen.
const dots = computed(() => {
  const all = pages.value.map((p) => ({ offset: p.offset }))
  if (all.length <= 7) return all
  const idx = -offset.value
  const from = Math.max(0, Math.min(all.length - 7, idx - 3))
  return all.slice(from, from + 7)
})

const groups = computed(() => daysOf(offset.value)
  .filter((d) => d.items.length)
  .reverse()
  .map((d) => ({ iso: d.iso, full: d.full, date: d.date, today: d.today, items: d.items })))

const cover = (r) => {
  const p = photosFor(r)[0]
  return p ? tileStyle(p) : {}
}

function onScroll() {
  const el = pagerEl.value
  if (!el || !el.clientWidth) return
  const idx = Math.round(el.scrollLeft / el.clientWidth)
  const next = -Math.max(0, Math.min(pages.value.length - 1, idx))
  if (next !== offset.value) {
    offset.value = next
    flash.value = null
    if (listEl.value) listEl.value.scrollTop = 0
  }
}

function scrollToPage(idx) {
  const el = pagerEl.value
  if (el) el.scrollTo({ left: idx * el.clientWidth, behavior: 'smooth' })
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

onMounted(() => { if (pagerEl.value) pagerEl.value.scrollLeft = 0 })
</script>

<style scoped>
.diary { position: relative; }
h1 { margin: 4px 0 0; font-size: 29px; letter-spacing: -0.8px; line-height: 1.08; }

.card { background: var(--card); border-radius: 20px; box-shadow: 0 1px 2px rgba(30, 42, 31, 0.06), 0 8px 22px rgba(30, 42, 31, 0.09); }

.cur-row { display: flex; align-items: center; gap: 8px; margin-top: 14px; min-height: 28px; }
.cur-tag { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: rgba(30, 42, 31, 0.07); color: var(--ink-2); }
.cur-tag.now { background: rgba(47, 107, 54, 0.12); color: var(--green); }
.cur-range { font-size: 13.5px; font-weight: 600; color: var(--ink-3); }
.jump { margin: -8px -6px -8px auto; height: 44px; padding: 0 6px; background: none; border: none; font-family: inherit; font-size: 13px; font-weight: 600; color: var(--green); cursor: pointer; }

.pager { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; margin: 8px -24px 0; padding: 4px 0 14px; }
.pager::-webkit-scrollbar { display: none; }
.page { flex: none; width: 100%; padding: 0 24px; scroll-snap-align: center; display: flex; flex-direction: column; gap: 12px; }

.week-days { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 2px; padding: 12px 6px 10px; }
.wd { display: flex; flex-direction: column; align-items: center; gap: 6px; background: none; border: none; padding: 0; font-family: inherit; cursor: pointer; }
.wd:disabled { cursor: default; }
.wd-letter { font-size: 11px; font-weight: 600; color: var(--ink-4); }
.wd-letter.today { color: var(--accent); }
.wd-date { width: 36px; height: 36px; border-radius: 999px; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 700; color: var(--ink-3); }
.wd-date.future { color: var(--ink-5); }
.wd-date.has { background: #E3EAE0; color: var(--ink); }
.wd-date.today { background: var(--dark); color: var(--paper); }
.wd-icons { display: flex; gap: 3px; height: 14px; align-items: center; color: var(--green); }

.stats { overflow: hidden; padding-bottom: 14px; }
.mins-row { display: flex; align-items: baseline; gap: 6px; padding: 18px 18px 0; }
.mins { font-family: var(--font-display); font-weight: 600; font-size: 44px; line-height: 1; letter-spacing: -1.5px; }
.mins-unit { font-size: 14px; font-weight: 600; color: var(--ink-3); }
.delta { padding: 0 18px; margin-top: 6px; font-size: 13px; font-weight: 600; color: var(--ink-4); }
.delta.up { color: var(--green); }
.delta.down { color: #B9661C; }
.pt.miss { width: 12px; height: 12px; background: #B9661C; }
.guilt { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 8px; margin: 16px 18px 6px; padding-top: 14px; border-top: 1px solid rgba(30, 42, 31, 0.08); }
.guilt-big { font-family: var(--font-display); font-weight: 600; font-size: 22px; letter-spacing: -0.4px; color: #B83A26; }
.guilt-line { font-size: 13px; font-weight: 600; line-height: 1.4; color: var(--ink); text-wrap: pretty; }

.curve { position: relative; margin: 14px 6px 0; }
.curve svg { position: absolute; inset: 0; overflow: visible; }
.grid { position: absolute; left: 0; right: 0; border-top: 1px solid rgba(30, 42, 31, 0.13); }
.grid.dashed { border-top-style: dashed; border-top-color: rgba(30, 42, 31, 0.2); }
.grid-label { position: absolute; right: 2px; font-size: 10px; font-weight: 600; color: var(--ink-4); }
.pt { position: absolute; width: 7px; height: 7px; transform: translate(-50%, -50%); border-radius: 999px; background: rgba(30, 42, 31, 0.2); box-shadow: 0 0 0 2.5px #fff; }
.pt.on { width: 11px; height: 11px; background: var(--green); }
.pt.on.today { background: var(--accent); }
.pt-label { position: absolute; transform: translateX(-50%); font-size: 11.5px; font-weight: 700; color: var(--ink); }

.dots { display: flex; justify-content: center; gap: 6px; padding: 0 0 4px; }
.dot { width: 6px; height: 6px; border-radius: 999px; background: rgba(30, 42, 31, 0.18); transition: width 0.2s; }
.dot.on { width: 20px; background: var(--green); }

.empty { margin-top: 12px; padding: 22px 18px; text-align: center; }
.empty-title { font-size: 15px; font-weight: 600; }
.empty-sub { margin-top: 4px; font-size: 13px; color: rgba(30, 42, 31, 0.55); }

.group { margin-top: 18px; border-radius: 16px; transition: background 0.4s ease; }
.group.flash { background: rgba(232, 145, 58, 0.14); }
.group-label { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--ink-4); }
.today-pill { padding: 3px 8px; border-radius: 999px; background: rgba(232, 145, 58, 0.15); color: #B9661C; font-size: 11px; letter-spacing: 0; text-transform: none; }
.entries { display: flex; flex-direction: column; gap: 10px; }

.entry { display: block; width: 100%; padding: 0; overflow: hidden; border: none; border-radius: 22px; background: var(--card); box-shadow: 0 1px 2px rgba(30, 42, 31, 0.05), 0 8px 22px rgba(30, 42, 31, 0.06); font-family: inherit; text-align: left; color: var(--ink); cursor: pointer; }
.entry:active { transform: scale(0.98); }
.photo { position: relative; display: block; height: 150px; background-color: rgba(47, 107, 54, 0.1); }
.kind-pill { position: absolute; left: 12px; top: 12px; display: flex; align-items: center; gap: 5px; height: 26px; padding: 0 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.92); font-size: 12px; font-weight: 600; color: var(--green); }
.photo-count { position: absolute; right: 12px; bottom: 12px; display: flex; align-items: center; gap: 4px; height: 24px; padding: 0 9px; border-radius: 999px; background: var(--ink); font-size: 11.5px; font-weight: 700; color: var(--paper); }
.entry-row { display: flex; align-items: center; gap: 12px; padding: 12px 14px; }
.icon-tile { width: 40px; height: 40px; flex: none; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: rgba(47, 107, 54, 0.1); color: var(--green); }
.entry-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.entry-title { font-size: 15.5px; font-weight: 600; }
.entry-sub { margin-top: 2px; font-size: 13px; color: rgba(30, 42, 31, 0.55); }
.fb { display: flex; align-items: center; gap: 4px; height: 26px; padding: 0 9px; border-radius: 999px; font-size: 12px; font-weight: 600; background: rgba(30, 42, 31, 0.06); color: rgba(30, 42, 31, 0.65); white-space: nowrap; }
.fb.fun { background: rgba(47, 107, 54, 0.1); color: var(--green); }

.quiet-note { margin: 18px 0 4px; font-size: 12.5px; color: var(--ink-4); text-align: center; }
</style>
