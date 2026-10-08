<template>
  <template v-if="mission && missionStore.status === 'done'">
    <AppHeader />

    <!-- End-of-mission photo (story 10.3): optional, taken by the parent. Green shell. -->
    <div v-if="missionStore.finishPhase === 'capture'" class="scroll-area capture">
      <div class="cap-art" aria-hidden="true">
        <div class="cap-sun"><span class="cheese">Say cheese!</span></div>
        <div class="cap-ring" />
      </div>
      <span class="badge-pill">Mission complete</span>
      <h1 class="cap-title">Well<br />played<span class="dot">!</span></h1>
      <p class="cap-sub">{{ mission.title }} · {{ mission.placeName }}</p>
      <div class="cap-stickers">
        <div class="sticker tasks"><b>{{ tasksDone }}/{{ mission.steps.length }}</b><span>tasks</span></div>
        <div class="sticker mins"><b>{{ mission.durationMin }}</b><span>min</span></div>
      </div>
      <div class="cap-actions">
        <p class="cap-q">Grab one photo for your week?</p>
        <div class="cap-row">
          <button class="take" @click="cameraOpen = true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8.5A2 2 0 0 1 6 6.5h2l1.5-2h5l1.5 2h2a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z M12 16.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" /></svg>
            Take a photo
          </button>
          <button class="skip" @click="missionStore.finishPhase = 'rate'">Skip</button>
        </div>
        <p class="cap-note">Saved only on this phone.</p>
      </div>
    </div>

    <div v-else class="scroll-area finished">
      <div class="hero">
        <div class="hero-sun" />
        <div class="hero-ring" />
        <div class="hero-tick">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2F6B36" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
        </div>
        <span class="badge-pill">{{ mission.visit ? 'Visit complete' : 'Mission complete' }}</span>
        <h1 class="hero-title">{{ mission.visit ? mission.placeName : mission.title }}</h1>
        <p class="hero-where">{{ mission.visit ? 'Indoor play' : mission.placeName }} · {{ dayLabel }}</p>
        <div class="stats">
          <div v-for="x in stats" :key="x.k" class="stat"><b>{{ x.v }}</b><span>{{ x.k }}</span></div>
        </div>
      </div>

      <div class="rate-head"><h2>How was it?</h2><span>Ask your kid</span></div>
      <!-- One-tap feedback from the child; tapping again clears it. Skipping is fine. -->
      <div class="ratings">
        <button
          v-for="opt in FEEDBACK_OPTIONS"
          :key="opt.id"
          class="rating"
          :class="{ on: feedback === opt.id }"
          :style="{ '--fb': FB_COLOR[opt.id] }"
          @click="feedback = feedback === opt.id ? null : opt.id"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="FEEDBACK_ICON[opt.id]" /></svg>
          <span>{{ opt.label }}</span>
        </button>
      </div>

      <!-- What will be written to the Week log, shown before it happens. -->
      <div class="added">
        <span class="added-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F2F1EC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6.5h16v13.5H4V6.5Z M4 10.5h16 M8.5 3.5v4 M15.5 3.5v4" /></svg>
        </span>
        <span class="added-text">
          <b>Added to your week</b>
          <span>{{ savedLine }}</span>
        </span>
      </div>

      <button class="see-week" @click="finish">
        See this week
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12h14 M12.5 6l6 6-6 6" /></svg>
      </button>
    </div>

    <CameraOverlay
      v-if="cameraOpen"
      prompt="End of mission"
      note="Saved only on this phone."
      @capture="onCapture"
      @cancel="cameraOpen = false"
      @error="cameraOpen = false"
    />
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area placeholder">
      <p class="eyebrow-accent">Play</p>
      <h1>No mission to finish</h1>
      <p class="subtitle">Finish a running mission first.</p>
    </div>
  </template>
</template>

<script setup>
// Shown once the last step is done: first an optional end-of-mission photo on
// a green screen, then a summary card and optional one-tap feedback from the
// child. An indoor-place visit skips the photo and has no tasks. Only here is
// a record written (D4) — with the run's runId, so its photos group under it.

import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CameraOverlay from '../components/CameraOverlay.vue'
import { useMissionStore } from '../missionStore'
import { useHistoryStore, FEEDBACK_OPTIONS, feedbackLabel, localIso } from '../historyStore'
import { usePhotoStore } from '../photoStore'
import { FEEDBACK_ICON } from '../taskIcons'

const FB_COLOR = { fun: '#2F6B36', boring: '#6B7368', too_hard: '#C4622D', too_easy: '#3D6E86' }

const router = useRouter()
const missionStore = useMissionStore()
const historyStore = useHistoryStore()
const photoStore = usePhotoStore()
const mission = computed(() => missionStore.active)

const feedback = ref(null) // deliberately unset — skipping is fine
const cameraOpen = ref(false)

const photoStepsCount = computed(() => mission.value?.steps.filter((s) => s.confirm === 'photo').length ?? 0)
const tasksDone = computed(() => Object.values(missionStore.results).filter((r) => r === 'done').length)
const photoCount = computed(() => photoStore.countForRun(missionStore.runId))
const dayLabel = computed(() => new Date().toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' }).replace(',', ''))
const dateLabel = computed(() => new Date().toLocaleDateString('en-AU', { day: 'numeric', month: 'short' }))

const stats = computed(() => {
  const m = mission.value
  if (m.visit) return [{ v: String(m.durationMin), k: 'minutes' }]
  return [
    { v: String(m.durationMin), k: 'minutes' },
    { v: `${tasksDone.value}/${m.steps.length}`, k: 'tasks' },
    { v: String(photoCount.value), k: photoCount.value === 1 ? 'photo' : 'photos' }
  ]
})

const savedLine = computed(() => {
  const m = mission.value
  const parts = [dateLabel.value, m.placeName, m.title.toLowerCase(), `${m.durationMin} min`]
  if (feedback.value) parts.push(feedbackLabel(feedback.value).toLowerCase())
  return parts.join(' · ')
})

// blob is already a clean JPEG (CameraOverlay redraws it through a canvas).
function onCapture(blob) {
  photoStore.addPhoto({ runId: missionStore.runId, blob, source: 'end', stepText: 'End of mission' })
  cameraOpen.value = false
  missionStore.finishPhase = 'rate'
}

function finish() {
  const m = mission.value
  historyStore.addRecord({
    runId: missionStore.runId,
    date: localIso(),
    time: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
    placeName: m.placeName,
    category: m.category,
    missionTitle: m.title,
    templateId: m.templateId,
    durationMin: m.durationMin,
    photoStepsCount: photoStepsCount.value,
    totalSteps: m.steps.length,
    feedback: feedback.value
  })
  // Reset only after the route has actually changed, so this screen doesn't
  // flash its "no mission" fallback while the navigation is still in flight.
  router.push('/week').then(() => missionStore.resetMission())
}
</script>

<style scoped>
.badge-pill {
  position: relative;
  align-self: flex-start;
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(242, 241, 236, 0.14);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: var(--paper);
}

/* ---- capture prompt (green shell) ---- */
.capture { position: relative; display: flex; flex-direction: column; gap: 14px; color: var(--paper); overflow-x: hidden; }

.cap-art { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.cap-sun { position: absolute; right: -90px; top: 120px; width: 300px; height: 300px; border-radius: 50%; background: var(--accent); }
.cheese { position: absolute; left: 44px; top: 128px; width: 130px; text-align: center; transform: rotate(-6deg); font-family: var(--font-display); font-weight: 700; font-size: 19px; letter-spacing: -0.3px; color: var(--ink); white-space: nowrap; }
.cap-ring { position: absolute; right: -30px; top: 180px; width: 180px; height: 180px; border-radius: 50%; border: 2px dashed rgba(30, 42, 31, 0.4); }

.cap-title { position: relative; margin: 0; font-family: var(--font-display); font-weight: 800; font-size: 64px; line-height: 0.88; letter-spacing: -2.8px; color: var(--paper); }
.cap-title .dot { color: var(--accent); }
.cap-sub { position: relative; font-size: 14px; color: rgba(242, 241, 236, 0.75); }

.cap-stickers { position: relative; flex: 1; min-height: 210px; }
.sticker { position: absolute; border-radius: 50%; color: var(--ink); display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10px 22px rgba(20, 40, 24, 0.3); }
.sticker b { font-family: var(--font-display); font-weight: 700; line-height: 1; }
.sticker span { margin-top: 2px; font-size: 10.5px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
.sticker.tasks { left: 6px; top: 30px; width: 96px; height: 96px; background: var(--paper); transform: rotate(-8deg); }
.sticker.tasks b { font-size: 28px; }
.sticker.mins { left: 96px; top: 118px; width: 84px; height: 84px; background: #B4D278; transform: rotate(6deg); }
.sticker.mins b { font-size: 24px; }

.cap-actions { position: relative; display: flex; flex-direction: column; gap: 10px; padding-bottom: 4px; }
.cap-q { font-family: var(--font-display); font-weight: 600; font-size: 20px; letter-spacing: -0.3px; }
.cap-row { display: flex; gap: 10px; }
.take { flex: 1; display: flex; align-items: center; justify-content: center; gap: 9px; height: 56px; border: none; border-radius: 999px; background: var(--paper); color: var(--ink); font-family: inherit; font-size: 16.5px; font-weight: 700; cursor: pointer; box-shadow: 0 10px 22px rgba(20, 40, 24, 0.25); }
.take:active { transform: scale(0.985); }
.skip { flex: none; width: 88px; height: 56px; border: none; border-radius: 999px; background: transparent; box-shadow: inset 0 0 0 1.5px rgba(242, 241, 236, 0.4); color: var(--paper); font-family: inherit; font-size: 15px; font-weight: 600; cursor: pointer; }
.cap-note { text-align: center; font-size: 12.5px; color: rgba(242, 241, 236, 0.65); }

/* ---- finished ---- */
.finished { display: flex; flex-direction: column; gap: 14px; }

.hero { position: relative; overflow: hidden; flex: none; display: flex; flex-direction: column; border-radius: 26px; background: var(--green); padding: 22px 20px 20px; color: var(--paper); }
.hero-sun { position: absolute; right: -46px; top: -46px; width: 170px; height: 170px; border-radius: 50%; background: var(--accent); opacity: 0.95; }
.hero-ring { position: absolute; right: -10px; top: -10px; width: 98px; height: 98px; border-radius: 50%; border: 2px dashed rgba(30, 42, 31, 0.35); }
.hero-tick { position: absolute; right: 22px; top: 24px; width: 46px; height: 46px; border-radius: 50%; background: var(--paper); display: flex; align-items: center; justify-content: center; }
.hero-title { position: relative; margin: 14px 0 4px; max-width: 220px; font-size: 34px; line-height: 1; letter-spacing: -1.2px; color: var(--paper); text-wrap: balance; }
.hero-where { position: relative; font-size: 13.5px; color: rgba(242, 241, 236, 0.75); }

.stats { position: relative; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 20px; }
.stat { padding: 11px 12px 10px; border-radius: 16px; background: rgba(242, 241, 236, 0.1); display: flex; flex-direction: column; }
.stat b { font-family: var(--font-display); font-weight: 600; font-size: 24px; line-height: 1; letter-spacing: -0.6px; }
.stat span { margin-top: 5px; font-size: 11.5px; font-weight: 600; color: rgba(242, 241, 236, 0.7); }

.rate-head { display: flex; align-items: baseline; justify-content: space-between; padding: 4px 2px 0; }
.rate-head h2 { margin: 0; font-weight: 700; font-size: 21px; letter-spacing: -0.4px; }
.rate-head span { font-size: 12.5px; font-weight: 600; color: rgba(30, 42, 31, 0.5); }

.ratings { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.rating {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 62px;
  padding: 0 14px;
  border: none;
  border-radius: 20px;
  background: #FFFFFF;
  box-shadow: 0 1px 0 rgba(30, 42, 31, 0.06);
  color: var(--fb);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.rating span { font-family: var(--font-display); font-size: 16.5px; font-weight: 600; color: var(--ink); }
.rating:active { transform: scale(0.96); }
.rating.on { background: var(--fb); color: #FFFFFF; transform: rotate(-1.5deg); box-shadow: 0 10px 20px color-mix(in srgb, var(--fb) 33%, transparent); }
.rating.on span { color: #FFFFFF; }

.added { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 18px; background: rgba(47, 107, 54, 0.08); }
.added-icon { flex: none; width: 34px; height: 34px; border-radius: 50%; background: var(--green); display: flex; align-items: center; justify-content: center; }
.added-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.added-text b { font-size: 13.5px; font-weight: 700; }
.added-text span { margin-top: 1px; font-size: 12.5px; color: rgba(30, 42, 31, 0.6); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.see-week { flex: none; display: flex; align-items: center; justify-content: center; gap: 9px; height: 56px; border: none; border-radius: 999px; background: var(--ink); color: var(--paper); font-family: inherit; font-size: 16.5px; font-weight: 600; cursor: pointer; box-shadow: 0 10px 24px rgba(30, 42, 31, 0.22); }
.see-week:active { transform: scale(0.985); }

.placeholder { display: flex; flex-direction: column; justify-content: center; text-align: center; padding: 0 8px; }
.placeholder h1 { margin-top: 4px; }
</style>
