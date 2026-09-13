<template>
  <template v-if="mission && missionStore.status === 'done'">
    <div class="progress-track top-progress">
      <div v-for="i in 3" :key="i" class="seg"><span style="width: 100%" /></div>
    </div>
    <p class="finished-label">Mission finished</p>

    <div class="scroll-area finished-scroll">
      <div class="check-circle">
        <svg width="26" height="26" viewBox="0 0 26 26">
          <path d="M5 13 L11 19 L21 6" fill="none" stroke="#27500A" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
      <h1 class="finished-title">{{ mission.title }}, done!</h1>
      <p class="subtitle">Ask Daniel — skipping the question is fine.</p>

      <p class="section-eyebrow" style="margin-top: 24px">How was it?</p>
      <div class="choice-grid">
        <button
          v-for="opt in FEEDBACK_OPTIONS"
          :key="opt.id"
          class="choice-option"
          :class="{ selected: feedback === opt.id }"
          @click="feedback = opt.id"
        >
          {{ opt.label }}
        </button>
      </div>

      <p class="section-eyebrow" style="margin-top: 20px">Saved automatically</p>
      <div class="note-card">
        <p>{{ dateLabel }} · {{ mission.placeName }} · {{ categoryLabelLower }}</p>
        <p style="margin-top: 4px">{{ mission.durationMin }} min · {{ photoStepsCount }} of {{ mission.steps.length }} steps confirmed by photo</p>
      </div>

      <p class="section-eyebrow" style="margin-top: 20px">Keepsake</p>
      <p class="body-text">Optional — saves to your own photo library only.</p>
    </div>

    <hr class="divider" style="margin-bottom: 16px" />
    <div class="btn-row">
      <button class="btn btn-secondary" disabled title="Photo capture isn't wired up yet">Add a photo</button>
      <button class="btn btn-primary" @click="finish">Done</button>
    </div>
  </template>

  <template v-else>
    <AppHeader plain />
    <div class="scroll-area placeholder">
      <p class="section-eyebrow">Plan</p>
      <h1>No mission to finish</h1>
      <p class="subtitle">Finish a running mission first.</p>
    </div>
  </template>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useMissionStore } from '../missionStore'
import { useHistoryStore } from '../historyStore'
import { FEEDBACK_OPTIONS } from '../historyStore'
import { categoryLabel } from '../store'

const router = useRouter()
const missionStore = useMissionStore()
const historyStore = useHistoryStore()
const mission = computed(() => missionStore.active)

const feedback = ref(null) // deliberately unset — skipping is fine

const photoStepsCount = computed(() => mission.value?.steps.filter((s) => s.confirm === 'photo').length ?? 0)
const categoryLabelLower = computed(() => categoryLabel(mission.value?.category ?? '').toLowerCase())
const dateLabel = computed(() => new Date().toLocaleDateString(undefined, { day: 'numeric', month: 'short' }))

function finish() {
  const m = mission.value
  historyStore.addRecord({
    date: new Date().toISOString().slice(0, 10),
    time: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
    placeName: m.placeName,
    category: m.category,
    missionTitle: m.title,
    durationMin: m.durationMin,
    photoStepsCount: photoStepsCount.value,
    totalSteps: m.steps.length,
    feedback: feedback.value
  })
  // Reset only after the route has actually changed, so this screen doesn't
  // flash its "no mission" fallback while the navigation is still in flight.
  router.push('/today').then(() => missionStore.resetMission())
}
</script>

<style scoped>
.top-progress { margin: 24px 24px 0; }

.finished-label {
  text-align: center;
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 10px;
}

.finished-scroll {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.check-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--green-light);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
}

.finished-title { color: var(--green-dark); margin-top: 18px; }

.choice-grid, .note-card, .body-text { width: 100%; text-align: left; }

.note-card p { font-size: 11.5px; }

.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; }
</style>
