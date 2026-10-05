<template>
  <template v-if="mission && missionStore.status === 'done'">
    <AppHeader />

    <!-- End-of-mission photo (story 10.3): optional, taken by the parent. -->
    <div v-if="phase === 'capture'" class="scroll-area capture">
      <p class="eyebrow-accent">Mission complete</p>
      <h1>Well played!</h1>
      <p class="subtitle">{{ mission.title }} · {{ mission.placeName }}</p>

      <div class="capture-art" aria-hidden="true">
        <span class="art-circle">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8.5A2 2 0 0 1 6 6.5h2l1.5-2h5l1.5 2h2a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z M12 16.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" /></svg>
          <span class="art-dot" />
        </span>
      </div>

      <button class="btn btn-primary pill-btn" @click="cameraOpen = true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8.5A2 2 0 0 1 6 6.5h2l1.5-2h5l1.5 2h2a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z M12 16.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" /></svg>
        Take a photo
      </button>
      <p class="capture-note">Saved only on this phone.</p>
      <button class="btn btn-outline pill-btn skip" @click="phase = 'rate'">Skip</button>
    </div>

    <CameraOverlay
      v-if="cameraOpen"
      prompt="End of mission"
      note="Saved only on this phone."
      @capture="onCapture"
      @cancel="cameraOpen = false"
      @error="cameraOpen = false"
    />

    <div v-else class="scroll-area">
      <p class="eyebrow-accent">How was it</p>
      <h1>Mission finished.</h1>
      <p class="subtitle">Ask your kid. Skipping is fine.</p>

      <!-- One-tap feedback from the child; tapping again clears it. Skipping is fine. -->
      <div class="choice-grid" style="margin-top: 18px">
        <button
          v-for="opt in FEEDBACK_OPTIONS"
          :key="opt.id"
          class="choice-option"
          :class="{ selected: feedback === opt.id }"
          @click="feedback = feedback === opt.id ? null : opt.id"
        >
          {{ opt.label }}
        </button>
      </div>

      <!-- What will be written to the Week log, shown before it happens. -->
      <div class="saved-card">
        <p class="eyebrow-accent">Saved automatically</p>
        <p class="saved-line">{{ savedLine }}</p>
      </div>

      <button class="btn btn-primary pill-btn" @click="finish">See this week</button>
    </div>
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
// Shown once the last step is done: first an optional end-of-mission photo,
// then optional one-tap feedback from the child. Only here is a record
// written (D4) — with the run's runId, so its photos group under it.

import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CameraOverlay from '../components/CameraOverlay.vue'
import { useMissionStore } from '../missionStore'
import { useHistoryStore, FEEDBACK_OPTIONS, feedbackLabel, localIso } from '../historyStore'
import { usePhotoStore } from '../photoStore'

const router = useRouter()
const missionStore = useMissionStore()
const historyStore = useHistoryStore()
const photoStore = usePhotoStore()
const mission = computed(() => missionStore.active)

const phase = ref('capture') // 'capture' | 'rate'
const feedback = ref(null) // deliberately unset — skipping is fine
const cameraOpen = ref(false)

const photoStepsCount = computed(() => mission.value?.steps.filter((s) => s.confirm === 'photo').length ?? 0)
const dateLabel = computed(() => new Date().toLocaleDateString('en-AU', { day: 'numeric', month: 'short' }))
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
  phase.value = 'rate'
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
.capture { display: flex; flex-direction: column; }

.capture-art {
  flex: 1;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.art-circle {
  position: relative;
  width: 170px;
  height: 170px;
  border-radius: 50%;
  background: rgba(47, 107, 54, 0.1);
  color: var(--green);
  display: flex;
  align-items: center;
  justify-content: center;
}

.art-dot { position: absolute; top: 22px; right: 26px; width: 12px; height: 12px; border-radius: 50%; background: var(--accent); }

.pill-btn { width: 100%; border-radius: 999px; }
.capture-note { text-align: center; font-size: 12.5px; color: var(--ink-4); margin: 10px 0 14px; }
.skip { height: 50px; font-size: 15.5px; box-shadow: inset 0 0 0 1.5px rgba(30, 42, 31, 0.2); }

.saved-card {
  margin: 18px 0 14px;
  background: var(--card);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  padding: 16px 18px;
}

.saved-card .eyebrow-accent { margin-bottom: 7px; }
.saved-line { font-size: 14.5px; line-height: 1.5; color: var(--ink-2); }

.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; }
</style>
