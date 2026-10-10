<template>
  <div class="cover" role="dialog" aria-modal="true" aria-labelledby="cover-title">
    <!-- Scenery: decoration only, placed by percentage so it scales with the screen. -->
    <div class="scenery" aria-hidden="true">
      <div class="glow"></div>
      <div class="sun"></div>
      <div class="cloud"></div>
      <div class="hill" style="left:-160px;right:-60px;top:49%;height:80%;background:#2A6031"></div>
      <div class="hill" style="left:120px;right:-220px;top:60%;height:80%;background:#265A2B"></div>
      <div class="hill" style="left:-200px;right:-100px;top:80%;height:60%;background:#1F4A24"></div>
      <div class="tree" style="left:24px;top:54%;width:30px;height:56px;background:#1E4322"></div>
      <div class="tree" style="left:52px;top:56.5%;width:22px;height:40px;background:#1E4322"></div>
      <div class="tree" style="right:26px;top:70%;width:26px;height:48px;background:#1B3F1F"></div>
    </div>

    <div ref="contentEl" class="content">
      <svg class="trail" aria-hidden="true" fill="none">
        <path :d="trail" stroke="rgba(242,241,236,.28)" stroke-width="2.5" stroke-dasharray="2 9" stroke-linecap="round" />
      </svg>

      <div class="hero">
        <div class="brand">
          <svg width="16" height="20" viewBox="0 0 16 20"><path d="M8 19.5S1 13 1 7.8a7 7 0 0 1 14 0C15 13 8 19.5 8 19.5Z" fill="#F2F1EC" /><circle cx="8" cy="7.6" r="2.6" fill="#E8913A" /></svg>
          <div class="brand-name">Active Together<span class="accent">.</span></div>
        </div>
        <h1 id="cover-title">
          <span class="underlined">Outside<span class="underline"></span></span> in<br />under a <span class="minute">minute</span><span class="accent">.</span>
        </h1>
        <p>We find a nearby park that fits the time you have, and give you something to play when you get there.</p>
      </div>

      <!-- The four steps, zig-zagging down whatever room is left between the
           headline and the button. One opens at a time. -->
      <div class="chips">
        <div v-for="c in chipList" :key="c.name" class="chip-wrap" :class="c.side">
          <div
            ref="chipEls"
            class="chip"
            :style="{
              borderColor: c.border,
              width: c.w,
              borderRadius: c.radius,
              opacity: c.op,
              transform: c.tf,
              boxShadow: c.shadow,
              transitionDelay: `${c.delay}, ${c.delay}, 0s, 0s, 0s, 0s`
            }"
            @click="pick(c.index)"
          >
            <div class="chip-inner">
              <div class="chip-row">
                <div class="chip-icon" :style="{ background: c.iconBg, borderRadius: c.iconR }">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" :stroke="c.iconFg" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="c.icon" /></svg>
                </div>
                <div v-if="!c.isOpen" class="chip-name">{{ c.name }}</div>
                <div v-else>
                  <div class="chip-label">{{ c.label }}</div>
                  <div class="chip-value">{{ c.value }}</div>
                </div>
              </div>
              <div class="chip-body" :style="{ maxHeight: c.isOpen ? '90px' : '0px', opacity: c.isOpen ? 1 : 0 }">
                <div class="chip-say">{{ c.say }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div ref="ctaEl" class="cta-area">
        <button type="button" class="cta" @click="emit('done')">
          Get started
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1E2A1F" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12h14 M12.5 6l6 6-6 6" /></svg>
        </button>
        <div class="cta-note">Free. No account needed.</div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Welcome cover, shown after every sign-in, before the four-slide
// walkthrough. Colours, copy and timings are the design's own (v4 landing).
// Layout is responsive rather than pixel-placed: headline at the top, the
// four step chips share the room that is left, Get started sits at the
// bottom, and on a very short screen the cover scrolls instead of letting
// anything overlap. The dotted trail is drawn through the chips' measured
// positions, so it follows the layout at any size.
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'

const emit = defineEmits(['done'])
const contentEl = ref(null)
const ctaEl = ref(null)
const chipEls = ref([])

const CHIPS = [
  { name: 'Set your play time', pillW: 214, label: 'Your time', value: '45 min · 32 to play', icon: 'M12 21a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z M12 9v4l2.5 2 M9.5 2.5h5', side: 'left', say: 'Tell us how long you have. Travel time comes off it, so every park leaves real play time.' },
  { name: 'Pick a nearby park', pillW: 216, label: 'Wattle Park', value: 'Toilets · Shade · Fenced', icon: 'M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z M12 11.9a2.4 2.4 0 1 0 0-4.8 2.4 2.4 0 0 0 0 4.8Z', side: 'right', say: 'See toilets, shade, fences, parking and dogs for each park before you leave.' },
  { name: 'Play a mission', pillW: 186, label: 'Mission', value: 'Find 5 kinds of leaf', icon: 'M5 21V4 M5 4h11l-2 4 2 4H5', side: 'left', say: 'A short step-by-step game that suits the place, so the kids actually play.' },
  { name: 'Log your week', pillW: 182, label: 'This week', value: '3 outings together', icon: 'M6.5 5h11a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3h-11a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3Z M3.5 10h17 M8 3v4 M16 3v4 M9 15l2 2 4-4', side: 'right', say: 'Every outing is logged, so you can see how active the week has been.' }
]

const shown = ref(false)
const open = ref(-1)
const textWidths = ref(null)
const trail = ref('')
let t1, t2, iv, ro, raf

function loop() {
  clearInterval(iv)
  iv = setInterval(() => { open.value = (open.value + 1) % 4 }, 3400)
}
function pick(i) {
  clearTimeout(t2)
  open.value = i
  loop()
}

// Dotted path through the centre of each chip, then down to the button.
function drawTrail() {
  const box = contentEl.value
  if (!box || !chipEls.value.length) return
  const origin = box.getBoundingClientRect()
  const pts = chipEls.value.map((el) => {
    const r = el.getBoundingClientRect()
    return { x: r.left - origin.left + r.width / 2, y: r.top - origin.top + Math.min(r.height, 58) / 2 }
  })
  const cta = ctaEl.value?.getBoundingClientRect()
  let d = `M${pts[0].x} ${pts[0].y}`
  for (let i = 1; i < pts.length; i++) {
    const p = pts[i - 1], q = pts[i]
    const bend = Math.max(20, (q.y - p.y) / 2)
    d += ` C ${p.x} ${p.y + bend}, ${q.x} ${q.y - bend}, ${q.x} ${q.y}`
  }
  if (cta) {
    const l = pts[pts.length - 1]
    const mid = origin.width / 2
    const end = cta.top - origin.top
    d += ` C ${l.x} ${l.y + 40}, ${mid} ${end - 30}, ${mid} ${end}`
  }
  trail.value = d
}

function scheduleTrail() {
  cancelAnimationFrame(raf)
  raf = requestAnimationFrame(drawTrail)
}

onMounted(() => {
  t1 = setTimeout(() => { shown.value = true }, 80)
  t2 = setTimeout(() => { open.value = 0; loop() }, 2600)
  const font = "600 17px 'Bricolage Grotesque'"
  const measure = () => {
    const ctx = document.createElement('canvas').getContext('2d')
    if (!ctx) return
    ctx.font = font
    textWidths.value = CHIPS.map(c => Math.ceil(ctx.measureText(c.name).width))
  }
  if (document.fonts?.load) document.fonts.load(font).then(measure, measure)
  else measure()
  // Redraw the trail whenever the layout moves: resize, a chip opening, fonts.
  if (typeof ResizeObserver !== 'undefined') {
    ro = new ResizeObserver(scheduleTrail)
    if (contentEl.value) ro.observe(contentEl.value)
    nextTick(() => chipEls.value.forEach((el) => ro.observe(el)))
  }
  nextTick(scheduleTrail)
})
onBeforeUnmount(() => { clearTimeout(t1); clearTimeout(t2); clearInterval(iv); ro?.disconnect(); cancelAnimationFrame(raf) })

const pillWidths = computed(() =>
  CHIPS.map((c, i) => (textWidths.value ? 1 + 7 + 42 + 12 + textWidths.value[i] + 20 + 1 : c.pillW))
)

const chipList = computed(() => {
  const o = open.value
  const on = shown.value
  return CHIPS.map((c, i) => {
    const isOpen = i === o
    return {
      ...c,
      index: i,
      isOpen,
      w: isOpen ? 'min(286px, 100%)' : pillWidths.value[i] + 'px',
      radius: isOpen ? '20px' : '30px',
      iconR: isOpen ? '13px' : '50%',
      shadow: isOpen ? '0 16px 30px rgba(10,25,12,.35)' : '0 8px 18px rgba(10,25,12,.2)',
      border: isOpen ? 'rgba(232,145,58,.7)' : 'rgba(242,241,236,.18)',
      iconBg: i % 2 ? 'rgba(168,200,106,.22)' : 'rgba(232,145,58,.22)',
      iconFg: i % 2 ? '#A8C86A' : '#E8913A',
      op: on ? 1 : 0,
      tf: on ? 'none' : 'translateY(18px) scale(.7)',
      delay: 0.5 + i * 0.45 + 's'
    }
  })
})
</script>

<style scoped>

.cover {
  position: absolute; inset: 0; z-index: 1200; background: #2F6B36;
  overflow-x: hidden; overflow-y: auto; font-family: var(--font-body); -webkit-font-smoothing: antialiased;
}

/* ---- scenery (decoration, scales with the screen) ---- */
.scenery { position: absolute; inset: 0; min-height: 100%; overflow: hidden; pointer-events: none; }
.glow { position: absolute; top: 40px; right: -80px; width: 300px; height: 300px; border-radius: 50%; background: radial-gradient(closest-side, rgba(232,145,58,.3), rgba(232,145,58,0)); }
.sun { position: absolute; top: clamp(90px, 16%, 140px); right: 40px; width: 56px; height: 56px; border-radius: 50%; background: #E8913A; }
.cloud { position: absolute; top: clamp(60px, 10.5%, 92px); right: -14px; width: 90px; height: 16px; border-radius: 999px; background: rgba(242,241,236,.12); }
.hill { position: absolute; border-radius: 50%; }
.tree { position: absolute; clip-path: polygon(50% 0,85% 45%,68% 45%,100% 90%,56% 90%,56% 100%,44% 100%,44% 90%,0 90%,32% 45%,15% 45%); }

/* ---- content: headline, chips, button, top to bottom ---- */
.content {
  position: relative;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: clamp(44px, 12vh, 104px) 22px max(28px, env(safe-area-inset-bottom, 0px) + 20px);
}

.trail { position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible; }

.hero { position: relative; padding: 0 2px; }
.brand { display: flex; align-items: center; gap: 9px; margin-bottom: clamp(16px, 3vh, 26px); }
.brand-name { font-family: 'Bricolage Grotesque', system-ui; font-weight: 600; font-size: 15.5px; color: #F2F1EC; }
.accent { color: #E8913A; }
h1 { margin: 0 0 10px; font-family: 'Bricolage Grotesque', system-ui; font-weight: 700; font-size: clamp(34px, 11vw, 42px); line-height: 1; letter-spacing: -1.7px; color: #F2F1EC; }
.underlined { position: relative; display: inline-block; }
.underline { position: absolute; left: -3px; right: -2px; bottom: -4px; height: 3px; border-radius: 3px; background: #E8913A; transform: rotate(-1deg); }
.minute { font-style: italic; font-weight: 600; color: #F5BF8C; }
.hero p { margin: 0; max-width: 300px; font-size: 15px; line-height: 1.45; color: rgba(242,241,236,.78); }

/* The chips take the room between headline and button, evenly spaced. */
.chips {
  position: relative;
  flex: 1 0 auto;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  gap: clamp(10px, 2.2vh, 22px);
  padding: clamp(18px, 3.5vh, 36px) 0;
}

.chip-wrap { display: flex; }
.chip-wrap.left { justify-content: flex-start; padding-left: 4px; }
.chip-wrap.right { justify-content: flex-end; padding-right: 0; }

.chip {
  max-width: 100%;
  cursor: pointer; color: #F2F1EC; overflow: hidden; box-sizing: border-box; padding: 7px;
  background: #2E6033; border: 1px solid;
  transition-property: opacity, transform, width, border-radius, box-shadow, border-color;
  transition-duration: .4s, .6s, .45s, .45s, .3s, .3s;
  transition-timing-function: ease, cubic-bezier(.34,1.7,.64,1), cubic-bezier(.2,.8,.2,1), ease, ease, ease;
}
.chip-inner { width: 270px; max-width: 100%; }
.chip-row { display: flex; align-items: center; gap: 12px; white-space: nowrap; }
.chip-icon { flex: none; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; transition: border-radius .45s ease; }
.chip-name { font-family: 'Bricolage Grotesque', system-ui; font-size: 17px; font-weight: 600; letter-spacing: -.3px; color: #F2F1EC; }
.chip-label { font-size: 10px; font-weight: 600; letter-spacing: 1.4px; text-transform: uppercase; color: rgba(242,241,236,.72); margin-bottom: 1px; }
.chip-value { font-family: 'Bricolage Grotesque', system-ui; font-size: 15px; font-weight: 600; letter-spacing: -.2px; color: #F2F1EC; }
.chip-body { overflow: hidden; transition: max-height .45s cubic-bezier(.2,.8,.2,1), opacity .35s ease .1s; }
.chip-say { padding: 8px 10px 4px 54px; font-size: 13.5px; line-height: 1.38; color: rgba(242,241,236,.88); text-wrap: pretty; white-space: normal; }

.cta-area { position: relative; margin-top: auto; padding: 0 2px; }
.cta {
  width: 100%; border: none; cursor: pointer; font-family: inherit;
  display: flex; align-items: center; justify-content: center; gap: 10px;
  height: 58px; border-radius: 999px; font-size: 17px; font-weight: 600; letter-spacing: -.2px;
  background: #E8913A; color: #1E2A1F; text-decoration: none;
  box-shadow: 0 10px 24px rgba(10,25,12,.3);
}
.cta:active { transform: scale(.985); }
.cta-note { margin-top: 12px; text-align: center; font-size: 12.5px; color: rgba(242,241,236,.72); }

/* Short screens (an iPhone with Safari's bars showing is ~660px): tighten
   the spacing and keep an open chip to its label and value, so the headline,
   all four steps and Get started fit without scrolling. */
@media (max-height: 760px) {
  .content { padding-top: clamp(28px, 6vh, 48px); }
  .brand { margin-bottom: 14px; }
  h1 { font-size: clamp(32px, 9.5vw, 38px); }
  .hero p { font-size: 14px; }
  .chips { padding: 14px 0; gap: 8px; }
  .chip-body { display: none; }
  .cta-note { margin-top: 8px; }
}
</style>
