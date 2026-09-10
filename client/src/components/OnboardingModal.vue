<template>
  <div class="onb-backdrop">
  <div class="onb" role="dialog" aria-modal="true" aria-labelledby="onb-title">
    <div class="onb-bar">
      <span class="onb-brand">
        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
          <circle cx="8" cy="8" r="8" fill="#3B6D11" />
          <circle cx="8" cy="8" r="3" fill="#FFFFFF" />
        </svg>
        Active Together.
      </span>
      <button class="onb-skip" type="button" @click="finish">Skip</button>
    </div>

    <div
      class="onb-track-wrap"
      @pointerdown="onDown"
      @pointermove="onMove"
      @pointerup="onUp"
      @pointercancel="onUp"
    >
      <div class="onb-track" :style="trackStyle">
        <section v-for="(s, i) in SLIDES" :key="s.key" class="onb-slide" :aria-hidden="i !== index">
          <div class="onb-art" :style="{ background: s.bg }">
            <component :is="s.art" />
          </div>
          <p class="onb-kicker">{{ s.kicker }}</p>
          <h2 :id="i === index ? 'onb-title' : undefined" class="onb-title">{{ s.title }}</h2>
          <p class="onb-body">{{ s.body }}</p>
          <p v-if="s.note" class="onb-note">{{ s.note }}</p>
        </section>
      </div>
    </div>

    <div class="onb-dots" aria-hidden="true">
      <span v-for="(s, i) in SLIDES" :key="s.key" :class="{ on: i === index }" />
    </div>
    <button class="btn btn-primary onb-btn" type="button" @click="next">
      {{ isLast ? "Choose where you're starting" : 'Next' }}
    </button>
  </div>
  </div>
</template>

<script setup>
import { computed, h, ref } from 'vue'

const emit = defineEmits(['done'])

// ---- illustrations (inline SVG render functions) ----

const svg = (children, bg) =>
  h('svg', { viewBox: '0 0 330 320', width: '100%', height: '100%', 'aria-hidden': 'true' }, children)

const Face = (cx, cy, r = 20) => [
  h('circle', { cx, cy, r, fill: '#FBF7EA' }),
  h('circle', { cx: cx - 7, cy: cy - 3, r: 2.5, fill: '#2C2C2A' }),
  h('circle', { cx: cx + 7, cy: cy - 3, r: 2.5, fill: '#2C2C2A' }),
  h('path', { d: `M${cx - 7} ${cy + 5} Q${cx} ${cy + 12} ${cx + 7} ${cy + 5}`, stroke: '#2C2C2A', 'stroke-width': 2, fill: 'none', 'stroke-linecap': 'round' }),
  h('circle', { cx: cx - 14, cy: cy + 5, r: 3.5, fill: '#F6C0A8' }),
  h('circle', { cx: cx + 14, cy: cy + 5, r: 3.5, fill: '#F6C0A8' })
]

const Sun = (cx, cy, r = 18, face = false) => [
  ...[0, 45, 90, 135, 180, 225, 270, 315].map((a) => {
    const rad = (a * Math.PI) / 180
    return h('line', {
      x1: cx + Math.cos(rad) * (r + 6), y1: cy + Math.sin(rad) * (r + 6),
      x2: cx + Math.cos(rad) * (r + 14), y2: cy + Math.sin(rad) * (r + 14),
      stroke: '#F4C542', 'stroke-width': 3, 'stroke-linecap': 'round'
    })
  }),
  h('circle', { cx, cy, r, fill: '#F9D65C' }),
  ...(face
    ? [
        h('circle', { cx: cx - 6, cy: cy - 3, r: 2, fill: '#2C2C2A' }),
        h('circle', { cx: cx + 6, cy: cy - 3, r: 2, fill: '#2C2C2A' }),
        h('path', { d: `M${cx - 6} ${cy + 4} Q${cx} ${cy + 10} ${cx + 6} ${cy + 4}`, stroke: '#2C2C2A', 'stroke-width': 1.8, fill: 'none', 'stroke-linecap': 'round' })
      ]
    : [])
]

const Cloud = (x, y, s = 1) =>
  h('g', { transform: `translate(${x} ${y}) scale(${s})` }, [
    h('ellipse', { cx: 0, cy: 0, rx: 26, ry: 12, fill: '#FFFFFF' }),
    h('circle', { cx: -8, cy: -6, r: 12, fill: '#FFFFFF' }),
    h('circle', { cx: 8, cy: -8, r: 14, fill: '#FFFFFF' })
  ])

const Tree = (x, y, s = 1) =>
  h('g', { transform: `translate(${x} ${y}) scale(${s})` }, [
    h('rect', { x: -3, y: 0, width: 6, height: 24, fill: '#8B5E34' }),
    h('circle', { cx: 0, cy: -6, r: 16, fill: '#7DB35A' }),
    h('circle', { cx: -8, cy: 2, r: 10, fill: '#7DB35A' }),
    h('circle', { cx: 8, cy: 2, r: 10, fill: '#7DB35A' })
  ])

const Pill = (cx, cy, text, w) => [
  h('rect', { x: cx - w / 2, y: cy - 18, width: w, height: 36, rx: 18, fill: '#3B6D11' }),
  h('text', { x: cx, y: cy + 5, 'text-anchor': 'middle', fill: '#FFFFFF', 'font-size': 14, 'font-weight': 700, 'font-family': 'inherit' }, text)
]

const ArtClock = () =>
  svg([
    h('rect', { width: 330, height: 320, fill: '#C3E3F1' }),
    Cloud(50, 40, 1.1), Cloud(180, 24, 0.9),
    ...Sun(276, 48, 22, true),
    h('path', { d: 'M0 240 Q165 200 330 240 L330 320 L0 320 Z', fill: '#8BC262' }),
    Tree(60, 250, 0.9),
    h('circle', { cx: 165, cy: 170, r: 78, fill: '#FBF7EA' }),
    h('circle', { cx: 165, cy: 170, r: 66, fill: '#FFFFFF' }),
    h('path', { d: 'M165 170 L165 104 A66 66 0 0 1 222 137 Z', fill: '#F5A94B' }),
    h('line', { x1: 165, y1: 170, x2: 165, y2: 118, stroke: '#3B6D11', 'stroke-width': 5, 'stroke-linecap': 'round' }),
    h('line', { x1: 165, y1: 170, x2: 210, y2: 145, stroke: '#3B6D11', 'stroke-width': 4, 'stroke-linecap': 'round' }),
    h('circle', { cx: 165, cy: 170, r: 4, fill: '#3B6D11' }),
    ...[104, 236].map((y) => h('circle', { cx: 165, cy: y, r: 3, fill: '#D24D3A' })),
    ...[99, 231].map((x) => h('circle', { cx: x, cy: 170, r: 3, fill: '#D24D3A' })),
    h('circle', { cx: 150, cy: 168, r: 2.5, fill: '#2C2C2A' }),
    h('circle', { cx: 180, cy: 168, r: 2.5, fill: '#2C2C2A' }),
    h('path', { d: 'M152 180 Q165 190 178 180', stroke: '#2C2C2A', 'stroke-width': 2, fill: 'none', 'stroke-linecap': 'round' }),
    h('circle', { cx: 140, cy: 180, r: 4, fill: '#F6C0A8' }),
    h('circle', { cx: 190, cy: 180, r: 4, fill: '#F6C0A8' }),
    ...Pill(165, 270, '45 min free', 120)
  ])

const ArtMap = () =>
  svg([
    h('rect', { width: 330, height: 320, fill: '#DDEBD0' }),
    ...Sun(45, 40, 14),
    Cloud(270, 30, 0.8),
    h('path', {
      d: 'M20 30 Q70 90 110 110 T160 180 T210 250 T300 300',
      stroke: '#FFFFFF', 'stroke-width': 8, fill: 'none', 'stroke-dasharray': '2 16', 'stroke-linecap': 'round'
    }),
    Tree(95, 90), Tree(265, 135), Tree(70, 230, 0.9),
    h('ellipse', { cx: 190, cy: 255, rx: 28, ry: 8, fill: 'rgba(0,0,0,0.12)' }),
    h('path', { d: 'M190 260 C150 210 138 190 138 165 A52 52 0 1 1 242 165 C242 190 230 210 190 260 Z', fill: '#B36B14' }),
    ...Face(190, 165, 28),
    ...Pill(165, 295, 'You are here', 100)
  ])

const ArtWeather = () =>
  svg([
    h('rect', { width: 330, height: 320, fill: '#C3E3F1' }),
    h('path', { d: 'M0 240 Q165 210 330 240 L330 320 L0 320 Z', fill: '#8BC262' }),
    ...Sun(110, 80, 26, true),
    h('ellipse', { cx: 190, cy: 195, rx: 66, ry: 10, fill: '#B7CFD9' }),
    h('g', [
      h('ellipse', { cx: 180, cy: 130, rx: 60, ry: 30, fill: '#FFFFFF' }),
      h('circle', { cx: 150, cy: 118, r: 28, fill: '#FFFFFF' }),
      h('circle', { cx: 190, cy: 100, r: 36, fill: '#FFFFFF' }),
      h('circle', { cx: 225, cy: 122, r: 26, fill: '#FFFFFF' })
    ]),
    h('circle', { cx: 176, cy: 120, r: 4, fill: '#2C2C2A' }),
    h('circle', { cx: 204, cy: 120, r: 4, fill: '#2C2C2A' }),
    h('circle', { cx: 176, cy: 120, r: 1.5, fill: '#FFFFFF' }),
    h('circle', { cx: 204, cy: 120, r: 1.5, fill: '#FFFFFF' }),
    h('path', { d: 'M178 136 Q190 146 202 136', stroke: '#2C2C2A', 'stroke-width': 2.2, fill: 'none', 'stroke-linecap': 'round' }),
    ...[165, 215].map((x) => h('path', { d: `M${x} 170 q-2 8 0 16`, stroke: '#7FB5D0', 'stroke-width': 3, fill: 'none', 'stroke-linecap': 'round' })),
    h('rect', { x: 36, y: 150, width: 68, height: 32, rx: 16, fill: '#FFFFFF' }),
    h('text', { x: 70, y: 172, 'text-anchor': 'middle', 'font-size': 16, 'font-weight': 700, fill: '#2C2C2A' }, '22°'),
    ...Pill(165, 285, 'Checked, not guessed', 160)
  ])

const Flag = (x, y, colour, n, h0 = 80) =>
  h('g', [
    h('rect', { x: x - 2, y, width: 4, height: h0, rx: 2, fill: '#7A5230' }),
    h('path', { d: `M${x + 2} ${y} L${x + 40} ${y + 12} L${x + 2} ${y + 24} Z`, fill: colour }),
    h('text', { x: x + 14, y: y + 16, 'font-size': 10, 'font-weight': 700, fill: '#FFFFFF' }, String(n))
  ])

const ArtFlags = () =>
  svg([
    h('rect', { width: 330, height: 320, fill: '#DDEBD0' }),
    ...Sun(278, 40, 14),
    h('path', { d: 'M0 130 Q165 100 330 120 L330 320 L0 320 Z', fill: '#8BC262' }),
    Flag(66, 130, '#E8604C', 1, 70),
    Flag(128, 110, '#3B6D11', 2, 90),
    Flag(190, 140, '#F5A94B', 3, 60),
    h('ellipse', { cx: 112, cy: 300, rx: 40, ry: 8, fill: 'rgba(0,0,0,0.12)' }),
    h('path', { d: 'M78 260 q-12 -10 4 -18', stroke: '#7DB35A', 'stroke-width': 9, 'stroke-linecap': 'round' }),
    h('circle', { cx: 112, cy: 262, r: 36, fill: '#7DB35A' }),
    ...[92, 132].map((x) => h('ellipse', { cx: x, cy: 296, rx: 10, ry: 6, fill: '#5C9438' })),
    h('circle', { cx: 100, cy: 258, r: 5, fill: '#FFFFFF' }), h('circle', { cx: 124, cy: 258, r: 5, fill: '#FFFFFF' }),
    h('circle', { cx: 101, cy: 259, r: 2.2, fill: '#2C2C2A' }), h('circle', { cx: 125, cy: 259, r: 2.2, fill: '#2C2C2A' }),
    h('path', { d: 'M102 272 Q112 280 122 272', stroke: '#2C2C2A', 'stroke-width': 2, fill: 'none', 'stroke-linecap': 'round' }),
    h('circle', { cx: 90, cy: 268, r: 4, fill: '#F6C0A8' }), h('circle', { cx: 134, cy: 268, r: 4, fill: '#F6C0A8' })
  ])

// ---- slides ----

const SLIDES = [
  {
    key: 'time',
    kicker: 'After school',
    title: 'Forty minutes free.',
    body: 'The gap between school and dinner. Long enough for a proper outing — if you know what to do when you get there.',
    art: ArtClock,
    bg: '#C3E3F1'
  },
  {
    key: 'data',
    kicker: 'Open data',
    title: 'Every park, mapped.',
    body: "Local councils publish where parks and playgrounds are. We bring them within walking or driving reach of wherever you're starting.",
    note: 'Melbourne, Monash and Melton so far.',
    art: ArtMap,
    bg: '#DDEBD0'
  },
  {
    key: 'weather',
    kicker: 'Checked for today',
    title: 'Weather counted in.',
    body: 'We check temperature, rain and wind for your window — so a plan that looks good on paper still works when you get there.',
    art: ArtWeather,
    bg: '#C3E3F1'
  },
  {
    key: 'plans',
    kicker: 'No fuss',
    title: 'Facts, then go.',
    body: "Three ready plans, each with a reason. Nothing about hours or cost we can't confirm. Nothing to sign up for.",
    art: ArtFlags,
    bg: '#DDEBD0'
  }
]

// ---- paging + swipe ----

const index = ref(0)
const isLast = computed(() => index.value === SLIDES.length - 1)

const dragX = ref(0)
const dragging = ref(false)
let startX = 0
let startY = 0
let wrapWidth = 1

const trackStyle = computed(() => ({
  transform: `translateX(calc(${-index.value * 100}% + ${dragX.value}px))`,
  transition: dragging.value ? 'none' : 'transform 0.28s ease'
}))

function onDown(e) {
  if (e.pointerType === 'mouse' && e.button !== 0) return
  dragging.value = true
  startX = e.clientX
  startY = e.clientY
  wrapWidth = e.currentTarget.clientWidth || 1
  e.currentTarget.setPointerCapture?.(e.pointerId)
}

function onMove(e) {
  if (!dragging.value) return
  const dx = e.clientX - startX
  // resist beyond the first/last slide
  const atEdge = (index.value === 0 && dx > 0) || (isLast.value && dx < 0)
  dragX.value = atEdge ? dx * 0.3 : dx
}

function onUp() {
  if (!dragging.value) return
  dragging.value = false
  const dx = dragX.value
  dragX.value = 0
  if (Math.abs(dx) < Math.max(40, wrapWidth * 0.15)) return
  if (dx < 0 && !isLast.value) index.value += 1
  else if (dx > 0 && index.value > 0) index.value -= 1
}

function next() {
  if (isLast.value) finish()
  else index.value += 1
}

function finish() {
  emit('done')
}
</script>

<style scoped>
/* Dimmed layer over the app; the card sits on top of it. */
.onb-backdrop {
  position: absolute;
  inset: 0;
  z-index: 1100; /* above Leaflet panes and controls (up to 1000) */
  background: rgba(23, 51, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

/* Mobile first: a card that fills the phone width with a small margin,
   capped so it stays a phone-sized dialog on wider screens. */
.onb {
  width: 100%;
  max-width: 390px;
  max-height: 100%;
  height: min(100%, 720px);
  background: #FBF9F2;
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(23, 51, 42, 0.35);
  display: flex;
  flex-direction: column;
  padding: 18px 22px 22px;
  overflow: hidden;
  animation: onb-in 0.28s ease;
}

@keyframes onb-in {
  from { opacity: 0; transform: translateY(16px) scale(0.98); }
  to { opacity: 1; transform: none; }
}

/* Very short viewports: keep the artwork from eating the copy. */
@media (max-height: 640px) {
  .onb-art { max-height: 34vh; }
  .onb-title { font-size: 22px; }
}

.onb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.onb-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--green-dark);
}

.onb-skip {
  background: none;
  border: none;
  font-family: inherit;
  font-size: 14px;
  color: var(--ink-4);
  cursor: pointer;
  padding: 4px;
}

.onb-track-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  margin: 0 -22px;
  touch-action: pan-y;
  cursor: grab;
  user-select: none;
}

.onb-track {
  display: flex;
  height: 100%;
  will-change: transform;
}

.onb-slide {
  flex: 0 0 100%;
  padding: 0 22px;
  overflow-y: auto;
}

.onb-art {
  aspect-ratio: 330 / 320;
  max-height: 42vh;
  width: 100%;
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 28px;
}

.onb-art svg { display: block; }

.onb-kicker {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--amber);
  margin-bottom: 6px;
}

.onb-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--green-dark);
  margin-bottom: 12px;
  line-height: 1.15;
}

.onb-body {
  font-size: 14px;
  line-height: 1.5;
  color: var(--ink-3);
}

.onb-note {
  font-size: 11.5px;
  color: var(--ink-5);
  margin-top: 8px;
}

.onb-dots {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 20px 0 16px;
}

.onb-dots span {
  width: 6px;
  height: 6px;
  border-radius: 3px;
  background: var(--line-3);
  transition: width 0.2s ease, background 0.2s ease;
}

.onb-dots span.on {
  width: 22px;
  background: var(--green);
}

.onb-btn {
  width: 100%;
  font-weight: 700;
  background: var(--green);
  color: #FFFFFF;
}
</style>
