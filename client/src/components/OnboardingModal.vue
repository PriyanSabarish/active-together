<template>
  <div class="onb" role="dialog" aria-modal="true" aria-labelledby="onb-title">
    <!-- Hero: shared landscape; the label and the mini preview card change per slide. -->
    <div class="onb-hero">
      <svg class="onb-sky" viewBox="0 0 390 300" preserveAspectRatio="none" aria-hidden="true">
        <rect width="390" height="300" fill="#E8F0DF" />
        <path d="M0 150 C 80 110, 160 175, 250 135 S 350 120, 390 150 L390 300 L0 300 Z" fill="#CFE3BE" />
        <path d="M0 210 C 110 180, 210 235, 390 195 L390 300 L0 300 Z" fill="#B9D9A0" />
      </svg>
      <!-- sun peeking over the far hill -->
      <span class="sun" />
      <!-- cloud -->
      <span class="cloud" /><span class="cloud-dot" />
      <!-- trees -->
      <svg class="trees" viewBox="0 0 390 300" aria-hidden="true">
        <g v-for="t in TREES" :key="t.x" :transform="`translate(${t.x} ${t.y}) scale(${t.s})`">
          <rect x="-2.5" y="30" width="5" height="12" fill="#8A5A2E" />
          <path d="M0 -6 L15 20 L-15 20 Z" fill="#2F6B36" />
          <path d="M0 6 L17 32 L-17 32 Z" fill="#276030" />
        </g>
        <ellipse cx="330" cy="262" rx="26" ry="4" fill="rgba(47,107,54,.18)" />
        <circle cx="300" cy="258" r="4" fill="rgba(47,107,54,.35)" /><circle cx="310" cy="262" r="3" fill="rgba(47,107,54,.3)" />
      </svg>

      <div class="onb-bar">
        <span class="onb-brand">
          <svg width="22" height="28" viewBox="0 0 100 126" aria-hidden="true"><path d="M50 2 C23 2 4 22 4 48 C4 82 50 124 50 124 C50 124 96 82 96 48 C96 22 77 2 50 2 Z" fill="var(--green)" /><circle cx="50" cy="34" r="12" fill="var(--accent)" /><path d="M28 54 Q50 70 72 54" fill="none" stroke="var(--paper)" stroke-width="10" stroke-linecap="round" /></svg>
          <b class="w-t">Active Together</b><b class="w-d">.</b>
        </span>
        <button class="onb-skip" type="button" @click="finish">Skip</button>
      </div>

      <p class="tab-label">{{ slide.tab }}</p>

    </div>

    <div
      ref="wrapEl"
      class="onb-track-wrap"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
    >
      <div class="onb-track" :style="trackStyle">
        <section v-for="(s, i) in SLIDES" :key="s.key" class="onb-slide" :aria-hidden="i !== index">
          <!-- Mini preview card: a static sketch of the screen each slide talks about. -->
          <div class="onb-mini" aria-hidden="true">
            <template v-if="s.key === 'start'">
              <p class="mini-eyebrow">Location</p>
              <div class="mini-loc">◎ Use my location</div>
              <p class="mini-eyebrow">Suburb</p>
              <div class="mini-chips small"><span class="on">Oakleigh</span><span>Clayton</span><span>Glen Waverley</span></div>
              <p class="mini-eyebrow">Distance</p>
              <div class="mini-chips"><span>3 km</span><span class="on">5 km</span><span>10 km</span></div>
            </template>

            <template v-else-if="s.key === 'options'">
              <p class="mini-eyebrow">Top options</p>
              <div v-for="r in PLACES" :key="r.name" class="mini-row">
                <span class="mini-ic"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="2.5" /></svg></span>
                <span class="mini-text"><b>{{ r.name }}</b><small>{{ r.sub }}</small></span>
              </div>
            </template>

            <template v-else-if="s.key === 'week'">
              <p class="mini-eyebrow">This week</p>
              <div class="mini-stats">
                <div class="mini-stat on"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 21V4M5 4h11l-2 4 2 4H5" /></svg><b>4</b><small>outings</small></div>
                <div class="mini-stat"><b>3</b><small>last week</small></div>
              </div>
              <p class="mini-eyebrow">Activity log</p>
              <div v-for="l in LOG" :key="l.day" class="mini-log">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M13 3.5 6.2 12.6a.6.6 0 0 0 .48.96h4.6l-1.28 7.04 6.8-9.1a.6.6 0 0 0-.48-.96h-4.6L13 3.5Z" /></svg>
                <span class="day">{{ l.day }}</span><span>{{ l.what }}</span>
              </div>
            </template>

            <template v-else>
              <p class="mini-eyebrow">Preferences</p>
              <div v-for="p in PREFS" :key="p.name" class="mini-row">
                <span class="mini-ic"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 20s-7-4.6-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.4-7 10-7 10z" /></svg></span>
                <span class="mini-text"><b>{{ p.name }}</b></span>
                <span class="mini-tag" :class="p.cls">{{ p.tag }}</span>
              </div>
            </template>
          </div>

          <!-- Mascot pin with a per-slide prop, sitting on the card's bottom-left corner. -->
          <span class="mascot">
            <svg width="120" height="110" viewBox="0 0 120 110" aria-hidden="true">
              <ellipse class="mascot-shadow" cx="52" cy="100" rx="30" ry="6" fill="rgba(30,42,31,.12)" />
              <g class="mascot-body">
              <!-- props -->
              <template v-if="s.key === 'start'">
                <circle cx="14" cy="34" r="4" fill="var(--accent)" opacity=".8" />
                <path d="M100 30 l6 12 h-12 z M100 38 l7 13 h-14 z" fill="var(--green)" /><rect x="98.5" y="51" width="3" height="6" fill="#8A5A2E" />
                <path d="M18 78 l5 10 h-10 z M18 84 l6 11 h-12 z" fill="var(--green)" /><rect x="16.5" y="95" width="3" height="5" fill="#8A5A2E" />
                <circle cx="96" cy="66" r="3" fill="rgba(47,107,54,.4)" /><circle cx="30" cy="70" r="2.5" fill="rgba(47,107,54,.4)" />
              </template>
              <template v-else-if="s.key === 'options'">
                <rect x="30" y="86" width="44" height="8" rx="4" fill="var(--accent)" />
                <circle cx="36" cy="96" r="6" fill="var(--dark)" /><circle cx="68" cy="96" r="6" fill="var(--dark)" />
                <line x1="88" y1="26" x2="88" y2="70" stroke="var(--green)" stroke-width="2.5" /><path d="M88 26 l18 6 -18 6 z" fill="var(--green)" />
                <line x1="14" y1="70" x2="14" y2="96" stroke="var(--accent)" stroke-width="2.5" /><path d="M14 70 l14 5 -14 5 z" fill="var(--accent)" />
                <circle cx="20" cy="30" r="4" fill="var(--accent)" opacity=".8" /><circle cx="104" cy="78" r="3" fill="rgba(47,107,54,.4)" />
              </template>
              <template v-else-if="s.key === 'week'">
                <g class="dumbbell">
                  <rect x="4" y="67" width="40" height="4" rx="2" fill="var(--dark)" />
                  <rect x="6" y="59" width="6" height="20" rx="2" fill="var(--dark)" /><rect x="12" y="62" width="4" height="14" rx="1.5" fill="var(--dark)" />
                  <rect x="36" y="59" width="6" height="20" rx="2" fill="var(--dark)" /><rect x="32" y="62" width="4" height="14" rx="1.5" fill="var(--dark)" />
                </g>
                <rect x="88" y="24" width="18" height="16" rx="3" fill="var(--accent)" /><rect x="88" y="24" width="18" height="5" rx="2" fill="#B8702A" />
                <circle cx="12" cy="30" r="4" fill="var(--accent)" opacity=".8" /><circle cx="104" cy="58" r="3" fill="rgba(47,107,54,.4)" />
              </template>
              <template v-else>
                <path d="M16 78 c-6-6-6-14 0-16 3-1 6 1 7 3 1-2 4-4 7-3 6 2 6 10 0 16 l-7 7 z" fill="var(--accent)" />
                <path d="M100 26 l3 8 8 3 -8 3 -3 8 -3-8 -8-3 8-3 z" fill="var(--green)" />
                <circle cx="14" cy="32" r="4" fill="var(--accent)" opacity=".8" /><circle cx="104" cy="62" r="3" fill="rgba(47,107,54,.4)" />
              </template>
              <!-- pin -->
              <g transform="translate(22 14) scale(0.62)">
                <path d="M50 2 C23 2 4 22 4 48 C4 82 50 124 50 124 C50 124 96 82 96 48 C96 22 77 2 50 2 Z" fill="var(--green)" />
                <template v-if="s.key === 'you'">
                  <path d="M30 40 c-4-6 4-12 8-6 4-6 12 0 8 6 l-8 8 z" fill="var(--dark)" />
                  <path d="M54 40 c-4-6 4-12 8-6 4-6 12 0 8 6 l-8 8 z" fill="var(--dark)" />
                </template>
                <template v-else>
                  <circle cx="38" cy="40" r="5" fill="var(--dark)" /><circle cx="62" cy="40" r="5" fill="var(--dark)" />
                </template>
                <circle cx="27" cy="52" r="5" fill="var(--accent)" opacity=".65" /><circle cx="73" cy="52" r="5" fill="var(--accent)" opacity=".65" />
                <path d="M36 56 Q50 70 64 56" fill="none" stroke="var(--paper)" stroke-width="6" stroke-linecap="round" />
              </g>
              </g>
            </svg>
          </span>
          <h2 :id="i === index ? 'onb-title' : undefined" class="onb-title">{{ s.title }}</h2>
          <p class="onb-body">{{ s.body }}</p>
        </section>
      </div>
    </div>

    <div class="onb-dots">
      <button v-for="(s, i) in SLIDES" :key="s.key" type="button" :class="{ on: i === index }" :aria-label="`Page ${i + 1}`" @click="index = i" />
    </div>
    <button class="btn btn-primary onb-btn" type="button" @click="next">
      {{ isLast ? 'Choose where you are starting' : 'Next' }} <span class="btn-arrow">→</span>
    </button>
  </div>
</template>

<script setup>
// Walkthrough, full screen over Start, shown after the cover on every sign-in.
// Four slides with the prototype's copy: a shared landscape hero, a tab label
// and a mini preview card per slide, the mascot with a small prop, title,
// body, dots and the button. Emits 'done' with 'setup' (last slide's button,
// goes into Start) or 'skip'. Swipe handling below supports mouse, pen and
// touch; touch uses non-passive listeners so a horizontal swipe can cancel
// page scroll.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const emit = defineEmits(['done'])

const SLIDES = [
  { key: 'start', tab: 'Start', title: 'Start with where you are.', body: 'Set your starting point and how far you will go. Takes a few seconds, once.' },
  { key: 'options', tab: 'Play', title: 'Get your top options.', body: 'Nearby places, each matched with a short mission for your child.' },
  { key: 'week', tab: 'Week', title: 'Do it, then see it.', body: 'Read a task out, they do it. What you did shows up on your week, automatically.' },
  { key: 'you', tab: 'You', title: 'Make it theirs.', body: 'Tune it to what your child likes — it quietly shapes what gets suggested next.' }
]

// hero trees: x, y (base), scale
const TREES = [
  { x: 14, y: 110, s: 1 },
  { x: 236, y: 102, s: 0.8 },
  { x: 374, y: 132, s: 0.85 },
  { x: 380, y: 188, s: 1.2 },
  { x: 318, y: 146, s: 1.15 },
  { x: 334, y: 178, s: 1.0 }
]

// mini-card sample content
const PLACES = [
  { name: 'Fawkner Park', sub: '0.6 km · good fit' },
  { name: 'Napier Park', sub: '1.4 km · good fit' },
  { name: 'Central Reserve', sub: '2.1 km · windy' }
]
const LOG = [
  { day: 'Mon', what: 'Fawkner Park · 22 min' },
  { day: 'Wed', what: 'Napier Park · 18 min' },
  { day: 'Fri', what: 'Central Reserve · 25 min' }
]
const PREFS = [
  { name: 'Playground', tag: 'Likes', cls: 'likes' },
  { name: 'Trail walking', tag: 'Likes', cls: 'likes' },
  { name: 'Cycling', tag: 'No preference', cls: 'neutral' },
  { name: 'Ball games', tag: 'Not for me', cls: 'nope' }
]

// ---- paging + swipe ----

const index = ref(0)
const isLast = computed(() => index.value === SLIDES.length - 1)
const slide = computed(() => SLIDES[index.value])

const wrapEl = ref(null)
const dragX = ref(0)
const dragging = ref(false)
let startX = 0
let startY = 0
let wrapWidth = 1
let axis = null // 'x' once we commit to a horizontal swipe, 'y' if we hand off to the browser

const trackStyle = computed(() => ({
  transform: `translateX(calc(${-index.value * 100}% + ${dragX.value}px))`,
  transition: dragging.value ? 'none' : 'transform 0.28s ease'
}))

function begin(x, y) {
  dragging.value = true
  axis = null
  startX = x
  startY = y
  wrapWidth = wrapEl.value?.clientWidth || 1
}

function move(x, y) {
  if (!dragging.value) return false
  const dx = x - startX
  const dy = y - startY
  if (!axis) {
    if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return false
    axis = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y'
  }
  if (axis !== 'x') return false
  // resist beyond the first/last slide
  const atEdge = (index.value === 0 && dx > 0) || (isLast.value && dx < 0)
  dragX.value = atEdge ? dx * 0.3 : dx
  return true
}

function end() {
  if (!dragging.value) return
  dragging.value = false
  const dx = dragX.value
  dragX.value = 0
  if (axis !== 'x' || Math.abs(dx) < Math.max(40, wrapWidth * 0.15)) return
  if (dx < 0 && !isLast.value) index.value += 1
  else if (dx > 0 && index.value > 0) index.value -= 1
}

// Mouse / pen: pointer events. Touch is handled below, because on phones the
// browser fires pointercancel as soon as it decides the finger is scrolling.
function onDown(e) {
  if (e.pointerType === 'touch') return
  if (e.pointerType === 'mouse' && e.button !== 0) return
  begin(e.clientX, e.clientY)
  e.currentTarget.setPointerCapture?.(e.pointerId)
}

function onMove(e) {
  if (e.pointerType === 'touch') return
  move(e.clientX, e.clientY)
}

function onUp(e) {
  if (e.pointerType === 'touch') return
  end()
}

// Touch: non-passive listeners so a horizontal swipe can preventDefault and
// keep the gesture instead of letting the page scroll.
function onTouchStart(e) {
  const t = e.touches[0]
  if (t) begin(t.clientX, t.clientY)
}

function onTouchMove(e) {
  const t = e.touches[0]
  if (t && move(t.clientX, t.clientY) && e.cancelable) e.preventDefault()
}

function onTouchEnd() {
  end()
}

onMounted(() => {
  const el = wrapEl.value
  el.addEventListener('touchstart', onTouchStart, { passive: true })
  el.addEventListener('touchmove', onTouchMove, { passive: false })
  el.addEventListener('touchend', onTouchEnd)
  el.addEventListener('touchcancel', onTouchEnd)
})

onBeforeUnmount(() => {
  const el = wrapEl.value
  if (!el) return
  el.removeEventListener('touchstart', onTouchStart)
  el.removeEventListener('touchmove', onTouchMove)
  el.removeEventListener('touchend', onTouchEnd)
  el.removeEventListener('touchcancel', onTouchEnd)
})

function next() {
  if (isLast.value) emit('done', 'setup')
  else index.value += 1
}

function finish() {
  emit('done', 'skip')
}
</script>

<style scoped>
/* Full-screen walkthrough over the app, as in the prototype. */
.onb {
  position: absolute;
  inset: 0;
  z-index: 1100; /* above Leaflet panes and controls (up to 1000) */
  background: var(--paper);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* hero */
.onb-hero {
  position: relative;
  height: 300px;
  flex-shrink: 0;
}

.onb-sky { position: absolute; inset: 0; width: 100%; height: 100%; border-radius: 0 0 28px 28px; }
.trees { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }

.sun {
  position: absolute;
  right: 22px;
  top: 96px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent);
  /* only the top half shows above the hill: clip with a gradient mask */
  -webkit-mask: linear-gradient(#000 0 52%, transparent 52%);
  mask: linear-gradient(#000 0 52%, transparent 52%);
}

.cloud { position: absolute; left: 218px; top: 100px; width: 46px; height: 16px; border-radius: 999px; background: #fff; }
.cloud::before { content: ''; position: absolute; left: 20px; top: -10px; width: 20px; height: 20px; border-radius: 50%; background: #fff; }
.cloud-dot { position: absolute; left: 272px; top: 112px; width: 7px; height: 7px; border-radius: 50%; background: #fff; }

.onb-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 44px 24px 0;
}

.onb-brand { display: inline-flex; align-items: center; gap: 8px; font-family: var(--font-display); font-size: 16px; }
.w-t { color: var(--ink); font-weight: 600; }
.w-d { color: var(--accent); font-weight: 700; }

.onb-skip {
  background: none;
  border: none;
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-3);
  cursor: pointer;
}

.tab-label {
  position: absolute;
  left: 24px;
  top: 158px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--green);
}

.onb-mini {
  position: relative;
  background: var(--card);
  border-radius: 22px;
  box-shadow: 0 14px 34px rgba(30, 42, 31, 0.16);
  padding: 18px 20px 20px;
  z-index: 2;
}

.mini-eyebrow { font-size: 11.5px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); margin: 0 0 10px; }
.mini-loc + .mini-eyebrow, .mini-chips + .mini-eyebrow, .mini-stats + .mini-eyebrow { margin-top: 14px; }

.mini-loc {
  padding: 13px 16px;
  border-radius: 12px;
  background: var(--green-light);
  color: var(--ink);
  font-size: 15px;
  font-weight: 600;
}

.mini-chips { display: flex; gap: 8px; }
.mini-chips span { flex: 1; text-align: center; padding: 14px 0; border-radius: 12px; background: var(--paper); font-size: 15px; font-weight: 600; color: var(--ink-3); white-space: nowrap; }
.mini-chips.small span { padding: 9px 0; font-size: 13.5px; }
.mini-chips span.on { background: var(--green); color: var(--paper); }

.mini-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px var(--line);
}

.mini-row + .mini-row { margin-top: 8px; }
.mini-ic { width: 40px; height: 40px; border-radius: 10px; background: var(--green-light); color: var(--green); display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mini-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.mini-text b { font-size: 15px; font-weight: 600; color: var(--ink); }
.mini-text small { font-size: 12.5px; color: var(--ink-3); margin-top: 2px; }

.mini-tag { padding: 5px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 600; white-space: nowrap; }
.mini-tag.likes { background: var(--green); color: var(--paper); }
.mini-tag.neutral { background: var(--tint); color: var(--ink-3); }
.mini-tag.nope { background: var(--amber-light); color: var(--amber); }

.mini-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mini-stat { border-radius: 14px; padding: 14px 14px 12px; background: var(--tint); color: var(--ink); display: flex; flex-direction: column; gap: 2px; }
.mini-stat.on { background: var(--green); color: var(--paper); }
.mini-stat svg { margin-bottom: 18px; }
.mini-stat b { font-family: var(--font-display); font-size: 26px; font-weight: 700; line-height: 1; }
.mini-stat small { font-size: 12.5px; opacity: 0.8; }

.mini-log { display: flex; align-items: center; gap: 8px; padding: 12px 0; border-top: 1px solid var(--line); font-size: 13.5px; color: var(--ink-3); }
.mini-log svg { color: var(--ink-5); }
.mini-log .day { font-weight: 700; color: var(--accent); }

/* slides */
/* Pulled up over the hero so each slide's card overlaps the landscape. */
.onb-track-wrap { flex: 1; min-height: 0; margin-top: -114px; overflow: hidden; touch-action: pan-y; }
.onb-track { display: flex; height: 100%; }

.onb-slide {
  flex: 0 0 100%;
  padding: 0 24px 0;
  display: flex;
  flex-direction: column;
}

/* The mascot overlaps the card's bottom-left corner; the card is 300-186 = 114px tall
   plus content, so this sits on the boundary regardless of slide height. */
/* Sits on the card's bottom-left corner and bobs gently; the shadow breathes with it. */
.mascot { display: block; margin: -36px 0 2px -8px; position: relative; z-index: 3; }
.mascot-body { animation: bob 3s ease-in-out infinite; }
.mascot-shadow { transform-box: fill-box; transform-origin: center; animation: breathe 3s ease-in-out infinite; }

@keyframes bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@keyframes breathe { 0%, 100% { transform: scaleX(1); opacity: 1; } 50% { transform: scaleX(0.85); opacity: 0.7; } }

@media (prefers-reduced-motion: reduce) {
  .mascot-body, .mascot-shadow { animation: none; }
}

.onb-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  line-height: 1.06;
  letter-spacing: -0.8px;
  margin: 0 0 10px;
}

.onb-body { font-size: 15.5px; line-height: 1.5; color: var(--ink-2); text-wrap: pretty; margin-bottom: 18px; }

/* dots + cta */
.onb-dots { display: flex; gap: 6px; padding: 0 24px 14px; }

.onb-dots button {
  width: 7px;
  height: 7px;
  padding: 0;
  border: none;
  border-radius: 999px;
  background: var(--line-3);
  cursor: pointer;
  transition: width 0.25s ease, background 0.25s ease;
}

.onb-dots button.on { width: 26px; background: var(--green); }

.onb-btn { margin: 0 24px calc(24px + env(safe-area-inset-bottom, 0px)); border-radius: 999px; }
</style>
