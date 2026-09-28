<template>
  <div class="cover" role="dialog" aria-modal="true" aria-labelledby="cover-title">
    <!-- backdrop: glow, sun, drifting clouds, hills and two swaying trees -->
    <span class="glow" />
    <span class="sun" />
    <span class="cloud c1" /><span class="cloud c2" />
    <svg class="hills" viewBox="0 0 390 280" preserveAspectRatio="xMidYMax slice" aria-hidden="true">
      <path d="M0 140 C60 102 124 102 184 132 C246 162 302 118 390 140 L390 280 L0 280 Z" fill="#276030" />
      <path d="M0 196 C70 168 142 178 212 194 C282 210 332 190 390 198 L390 280 L0 280 Z" fill="#1F5127" />
      <path class="trail" d="M-10 250 C60 230 110 214 170 222 C230 230 262 208 300 196" fill="none" stroke="rgba(242,241,236,.35)" stroke-width="2" stroke-dasharray="4 6" />
      <circle cx="300" cy="196" r="4" fill="#E8913A" />
      <g class="tree a">
        <rect x="46" y="164" width="4" height="14" fill="#14361A" />
        <path d="M48 116 L62 146 L34 146 Z" fill="#14361A" /><path d="M48 134 L64 166 L32 166 Z" fill="#14361A" />
      </g>
      <g class="tree b">
        <rect x="322" y="180" width="4" height="14" fill="#14361A" />
        <path d="M324 134 L338 164 L310 164 Z" fill="#14361A" /><path d="M324 152 L340 182 L308 182 Z" fill="#14361A" />
      </g>
    </svg>

    <div class="content">
      <p class="brand rise">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 22s7.5-7.6 7.5-13A7.5 7.5 0 1 0 4.5 9c0 5.4 7.5 13 7.5 13z" fill="#F2F1EC" /><circle cx="12" cy="9" r="3.1" fill="#E8913A" /></svg>
        Active Together<span class="dot">.</span>
      </p>

      <h1 id="cover-title" class="title rise">
        <span class="underlined">Outside<svg viewBox="0 0 200 20" preserveAspectRatio="none" aria-hidden="true"><path d="M4 12 C50 4 110 4 196 10" /></svg></span> in<br />
        under a <em>minute</em><span class="bounce">.</span>
      </h1>
      <p class="lede rise">We find a nearby park that fits the time you have, and give you something to play when you get there.</p>

      <!-- Four steps on a dotted path; one expands at a time, the first by default. -->
      <div class="steps">
        <svg class="path" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <path d="M15 0 C15 20 85 14 85 33 C85 52 15 46 15 66 C15 86 85 80 85 100" fill="none" stroke="rgba(242,241,236,.35)" stroke-width="1.6" stroke-dasharray="3 5" vector-effect="non-scaling-stroke" />
        </svg>
        <button
          v-for="(s, i) in STEPS"
          :key="s.key"
          type="button"
          class="step rise"
          :class="[i % 2 ? 'right' : 'left', { open: open === i }]"
          :style="{ animationDelay: `${0.22 + i * 0.08}s` }"
          @click="open = open === i ? -1 : i"
        >
          <span class="step-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E8913A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path :d="s.icon" /></svg></span>
          <template v-if="open === i">
            <span class="step-text">
              <span class="step-kicker">{{ s.kicker }}</span>
              <span class="step-title">{{ s.title }}</span>
              <span class="step-body">{{ s.body }}</span>
            </span>
          </template>
          <span v-else class="step-label">{{ s.label }}</span>
        </button>
      </div>
    </div>

    <div class="cta-wrap rise">
      <button type="button" class="cta" @click="emit('done')">
        Get started
        <svg class="nudge" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
      </button>
      <p class="fine">Free. No account needed.</p>
    </div>
  </div>
</template>

<script setup>
// Landing cover, the first thing a new user sees after the pilot gate and
// before the four-slide walkthrough. Dark green, one headline, the four
// stages of an outing as tappable pills, and a single "Get started". Purely
// informational: it stores nothing and only emits 'done'.
import { ref } from 'vue'

const emit = defineEmits(['done'])

const STEPS = [
  {
    key: 'time',
    label: 'Set your play time',
    kicker: 'Your time',
    title: '45 min · 25 to play',
    body: 'Tell us how long you have. Travel comes off the top, so every park leaves real play time.',
    icon: 'M12 5a8 8 0 1 0 0 16 8 8 0 0 0 0-16z M12 9v4l2.5 2 M9 2h6'
  },
  {
    key: 'picks',
    label: 'Pick a nearby park',
    kicker: 'Three picks',
    title: 'Ranked for today',
    body: 'Real spots near you, checked for weather, shade and air quality.',
    icon: 'M12 21s6.5-6.3 6.5-11.5a6.5 6.5 0 1 0-13 0C5.5 14.7 12 21 12 21z M12 9.5m-2.3 0a2.3 2.3 0 1 0 4.6 0 2.3 2.3 0 1 0-4.6 0'
  },
  {
    key: 'mission',
    label: 'Play a mission',
    kicker: 'At the park',
    title: 'A mission to do there',
    body: 'Short steps you read out, so the kids actually play once you arrive.',
    icon: 'M5 21V4 M5 4h11l-2 4 2 4H5'
  },
  {
    key: 'week',
    label: 'Log your week',
    kicker: 'This week',
    title: 'Minutes, together',
    body: 'Every outing is logged, so you can see how active the week has been.',
    icon: 'M3.5 5h17v15h-17z M3.5 10h17 M8 3v4 M16 3v4 M8 14h3'
  }
]

const open = ref(0)
</script>

<style scoped>
.cover {
  position: absolute;
  inset: 0;
  z-index: 1200; /* above the walkthrough (1100) */
  background: var(--green);
  color: var(--paper);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 52px 0 22px;
}

/* backdrop */
.glow {
  position: absolute;
  right: -60px;
  top: 40px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232, 145, 58, 0.45), rgba(232, 145, 58, 0) 70%);
  animation: glow 5s ease-in-out infinite;
}

.sun {
  position: absolute;
  right: 28px;
  top: 108px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent);
  animation: sunUp 1.2s cubic-bezier(0.2, 0.9, 0.3, 1) 0.2s backwards;
}

.cloud {
  position: absolute;
  border-radius: 12px;
  background: rgba(242, 241, 236, 0.14);
  animation: cloud 38s linear infinite;
}

.c1 { top: 66px; width: 64px; height: 16px; }
.c2 { top: 90px; width: 92px; height: 18px; background: rgba(242, 241, 236, 0.1); animation-duration: 52s; animation-delay: -20s; }

.hills { position: absolute; left: 0; right: 0; bottom: 0; width: 100%; height: 280px; }
.trail { animation: dash 3s linear infinite; }
.tree { transform-box: fill-box; transform-origin: 50% 100%; animation: sway 4s ease-in-out infinite; }
.tree.b { animation-duration: 4.6s; animation-delay: -1.3s; }

/* content */
.content { position: relative; flex: 1; min-height: 0; padding: 80px 24px 0; display: flex; flex-direction: column; }

.brand { display: flex; align-items: center; gap: 8px; padding-left: 4px; font-size: 14px; font-weight: 600; }
.dot { color: var(--accent); }

.title {
  margin: 14px 0 0;
  padding-left: 4px;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 42px;
  line-height: 0.98;
  letter-spacing: -1.2px;
  color: var(--paper);
  animation-delay: 0.08s;
}

.title em { font-style: italic; font-weight: 600; color: #F5C48A; }
.bounce { color: var(--accent); display: inline-block; animation: bounce 1.6s ease-in-out 1.4s infinite; }

.underlined { position: relative; display: inline-block; }
.underlined svg { position: absolute; left: -4px; bottom: -6px; width: calc(100% + 8px); height: 14px; }
.underlined path { stroke: var(--accent); stroke-width: 5; stroke-linecap: round; fill: none; stroke-dasharray: 260; animation: draw 0.8s cubic-bezier(0.6, 0, 0.3, 1) 0.6s backwards; }

.lede { margin-top: 14px; padding-left: 4px; font-size: 14px; line-height: 1.45; color: rgba(242, 241, 236, 0.72); max-width: 300px; animation-delay: 0.14s; }

/* steps */
.steps { position: relative; margin-top: 22px; display: flex; flex-direction: column; gap: 14px; }
.path { position: absolute; left: 30px; top: 10px; width: calc(100% - 60px); height: calc(100% - 20px); }
.path path { animation: dash 3s linear infinite; }

.step {
  position: relative;
  display: inline-flex;
  align-items: flex-start;
  gap: 10px;
  padding: 5px 16px 5px 5px;
  border: none;
  border-radius: 999px;
  background: rgba(242, 241, 236, 0.1);
  color: var(--paper);
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.16s ease;
}

.step:hover { background: rgba(242, 241, 236, 0.16); }
.step.left { align-self: flex-start; }
.step.right { align-self: flex-end; }
.step.open { width: 250px; padding: 12px 14px 14px; border-radius: 18px; background: rgba(242, 241, 236, 0.12); flex-wrap: wrap; }

.step-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(232, 145, 58, 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-label { font-size: 14.5px; font-weight: 600; line-height: 30px; }
.step-text { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.step-kicker { font-size: 10.5px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: var(--accent); }
.step-title { font-family: var(--font-display); font-size: 15.5px; font-weight: 600; line-height: 1.2; margin-top: 2px; }
.step-body { flex-basis: 100%; margin-top: 8px; font-size: 13px; line-height: 1.45; color: rgba(242, 241, 236, 0.72); }

/* cta */
.cta-wrap { position: relative; padding: 16px 24px 0; animation-delay: 0.56s; }

.cta {
  width: 100%;
  height: 56px;
  border: none;
  border-radius: 999px;
  background: var(--accent);
  color: var(--dark);
  font-family: inherit;
  font-size: 17px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.16s ease;
}

.cta:hover { background: #F09D48; }
.nudge { animation: nudge 1.4s ease-in-out infinite; }
.fine { padding-top: 12px; text-align: center; font-size: 13px; color: rgba(242, 241, 236, 0.6); }

/* motion */
.rise { animation-name: rise; animation-duration: 0.5s; animation-timing-function: ease; animation-fill-mode: backwards; }

@keyframes rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes glow { 0%, 100% { opacity: 0.35; } 50% { opacity: 0.6; } }
@keyframes sunUp { from { transform: translateY(60px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
@keyframes cloud { from { transform: translateX(-100px); } to { transform: translateX(480px); } }
@keyframes dash { to { stroke-dashoffset: -40; } }
@keyframes sway { 0%, 100% { transform: rotate(-2.5deg); } 50% { transform: rotate(2.5deg); } }
@keyframes draw { from { stroke-dashoffset: 260; } to { stroke-dashoffset: 0; } }
@keyframes bounce { 0%, 100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-4px) scale(1.08); } }
@keyframes nudge { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(4px); } }

@media (prefers-reduced-motion: reduce) {
  .rise, .glow, .sun, .cloud, .trail, .tree, .path path, .underlined path, .bounce, .nudge { animation: none; }
}
</style>
