<template>
  <div class="onb" role="dialog" aria-modal="true" aria-labelledby="onb-title">
    <!-- hero: shared landscape, slide-specific mini preview -->
    <div class="onb-hero">
      <svg class="onb-sky" viewBox="0 0 390 300" preserveAspectRatio="none" aria-hidden="true">
        <rect width="390" height="300" fill="#E4EEDD" />
        <circle cx="330" cy="120" r="34" fill="var(--accent)" />
        <path d="M0 190 C 90 150, 170 220, 260 175 S 360 150, 390 180 L390 300 L0 300 Z" fill="#CFE3BE" />
        <path d="M0 235 C 120 200, 220 260, 390 220 L390 300 L0 300 Z" fill="#B9D9A0" />
        <ellipse cx="230" cy="95" rx="26" ry="10" fill="#fff" opacity=".9" /><circle cx="248" cy="92" r="12" fill="#fff" opacity=".9" />
      </svg>
      <span class="tree t1" /><span class="tree t2" /><span class="tree t3" /><span class="tree t4" />

      <div class="onb-bar">
        <span class="onb-brand"><b class="w-a">Active</b> <b class="w-t">Together</b><b class="w-d">.</b></span>
        <button class="onb-skip" type="button" @click="finish">Skip</button>
      </div>

      <div class="onb-mini" aria-hidden="true">
        <template v-if="slide.key === 'start'">
          <p class="mini-eyebrow">Location</p>
          <div class="mini-row on">◎ Use my location</div>
          <p class="mini-eyebrow">Distance</p>
          <div class="mini-chips"><span>3 km</span><span class="on">5 km</span><span>10 km</span></div>
        </template>
        <template v-else-if="slide.key === 'options'">
          <p class="mini-eyebrow">Top options</p>
          <div class="mini-row"><b>Fawkner Park</b><span class="mini-tag">good fit</span></div>
          <div class="mini-row"><b>Napier Park</b><span class="mini-tag">good fit</span></div>
          <div class="mini-row"><b>Central Reserve</b><span class="mini-tag warn">windy</span></div>
        </template>
        <template v-else-if="slide.key === 'play'">
          <p class="mini-eyebrow">Task 1 of 5</p>
          <div class="mini-step">Stand where your shadow is longest.</div>
          <div class="mini-cta">Done</div>
        </template>
        <template v-else>
          <p class="mini-eyebrow">What Daniel likes</p>
          <div class="mini-row"><b>Playground</b><span class="mini-tag">Likes</span></div>
          <div class="mini-row"><b>Ball games</b><span class="mini-tag warn">Not for me</span></div>
        </template>
      </div>
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
          <span class="mascot" :class="{ happy: i === SLIDES.length - 1 }">
            <svg width="72" height="88" viewBox="0 0 100 126" aria-hidden="true">
              <path d="M50 2 C23 2 4 22 4 48 C4 82 50 124 50 124 C50 124 96 82 96 48 C96 22 77 2 50 2 Z" fill="var(--green)" />
              <template v-if="i === SLIDES.length - 1">
                <path d="M30 40 q8 -10 16 0" fill="none" stroke="var(--paper)" stroke-width="6" stroke-linecap="round" />
                <path d="M54 40 q8 -10 16 0" fill="none" stroke="var(--paper)" stroke-width="6" stroke-linecap="round" />
              </template>
              <template v-else>
                <circle cx="38" cy="40" r="5" fill="var(--paper)" /><circle cx="62" cy="40" r="5" fill="var(--paper)" />
              </template>
              <circle cx="28" cy="52" r="5" fill="var(--accent)" opacity=".7" /><circle cx="72" cy="52" r="5" fill="var(--accent)" opacity=".7" />
              <path d="M34 58 Q50 74 66 58" fill="none" stroke="var(--paper)" stroke-width="7" stroke-linecap="round" />
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
      {{ isLast ? 'Choose where you are starting' : 'Next' }}
    </button>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const emit = defineEmits(['done'])

// ---- slides (copy from the Canvas intro) ----

const SLIDES = [
  { key: 'start', title: 'Start with where you are.', body: 'Set your starting point and how far you will go. Takes a few seconds, once.' },
  { key: 'options', title: 'Get your top options.', body: 'Nearby places, each matched with a short mission for your child.' },
  { key: 'play', title: 'Do it, then see it.', body: 'Read a task out, they do it. What you did shows up on your week, automatically.' },
  { key: 'you', title: 'Make it theirs.', body: 'Tune it to what your child likes — it quietly shapes what gets suggested next.' }
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
  overflow: hidden;
  border-radius: 0 0 28px 28px;
}

.onb-sky { position: absolute; inset: 0; width: 100%; height: 100%; }

.tree {
  position: absolute;
  width: 0;
  height: 0;
  border-left: 14px solid transparent;
  border-right: 14px solid transparent;
  border-bottom: 44px solid var(--green);
}

.tree::after {
  content: '';
  position: absolute;
  left: -3px;
  top: 44px;
  width: 6px;
  height: 12px;
  background: #8A5A2E;
}

.t1 { left: 24px; top: 138px; transform: scale(0.8); }
.t2 { left: 250px; top: 128px; }
.t3 { left: 296px; top: 150px; transform: scale(0.75); }
.t4 { left: 120px; top: 96px; transform: scale(0.55); }

.onb-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 0;
}

.onb-brand { font-family: var(--font-display); font-size: 15px; font-weight: 600; }
.w-a { color: var(--green); }
.w-t { color: var(--ink); }
.w-d { color: var(--accent); }

.onb-skip {
  background: none;
  border: none;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-3);
  cursor: pointer;
}

.onb-mini {
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: -6px;
  background: var(--card);
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -6px 24px rgba(30, 42, 31, 0.12);
  padding: 16px 18px 14px;
}

.mini-eyebrow { font-size: 10.5px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); margin: 0 0 8px; }
.mini-eyebrow + .mini-eyebrow, .mini-row + .mini-eyebrow, .mini-chips + .mini-eyebrow { margin-top: 12px; }

.mini-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 11px;
  background: var(--paper);
  font-size: 13px;
  color: var(--ink-2);
}

.mini-row + .mini-row { margin-top: 6px; }
.mini-row.on { background: var(--green-light); color: var(--green-dark); font-weight: 600; }
.mini-row b { font-weight: 600; color: var(--ink); }

.mini-tag { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 600; background: rgba(47, 107, 54, 0.14); color: var(--green); }
.mini-tag.warn { background: var(--amber-light); color: var(--amber); }

.mini-chips { display: flex; gap: 6px; }
.mini-chips span { flex: 1; text-align: center; padding: 8px 0; border-radius: 11px; background: var(--paper); font-size: 13px; font-weight: 600; color: var(--ink-3); }
.mini-chips span.on { background: var(--green); color: var(--paper); }

.mini-step { font-family: var(--font-display); font-size: 17px; font-weight: 600; letter-spacing: -0.3px; line-height: 1.2; }
.mini-cta { margin-top: 10px; padding: 9px 0; text-align: center; border-radius: 11px; background: var(--accent); color: var(--dark); font-size: 13px; font-weight: 700; }

/* slides */
.onb-track-wrap { flex: 1; min-height: 0; overflow: hidden; touch-action: pan-y; }
.onb-track { display: flex; height: 100%; }

.onb-slide {
  flex: 0 0 100%;
  padding: 26px 28px 0;
  display: flex;
  flex-direction: column;
}

.mascot { display: inline-block; margin-bottom: 14px; filter: drop-shadow(0 8px 14px rgba(47, 107, 54, 0.25)); }

.onb-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 700;
  line-height: 1.06;
  letter-spacing: -0.8px;
  margin: 0 0 10px;
}

.onb-body { font-size: 15.5px; line-height: 1.5; color: var(--ink-2); text-wrap: pretty; }

/* dots + cta */
.onb-dots { display: flex; gap: 6px; padding: 0 28px 14px; }

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

.onb-dots button.on { width: 26px; background: var(--green); animation: obPulse 1.6s ease-in-out infinite; }

@keyframes obPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}

.onb-btn { margin: 0 24px calc(24px + env(safe-area-inset-bottom, 0px)); }
</style>
