<template>
  <template v-if="mission && missionStore.status === 'done'">
    <AppHeader />

    <div class="scroll-area">
      <p class="eyebrow-accent">How was it</p>
      <h1>Mission finished.</h1>
      <p class="subtitle">Ask Daniel. Skipping is fine.</p>

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

      <div class="saved-card">
        <p class="eyebrow-accent">Saved automatically</p>
        <p class="saved-line">{{ dateLabel }} · {{ mission.placeName }} · {{ mission.title.toLowerCase() }} · {{ mission.durationMin }} min</p>
        <p class="saved-sub">{{ photoStepsCount }} of {{ mission.steps.length }} steps confirmed by photo · {{ categoryLabelLower }}</p>
      </div>

      <p class="photo-note">Add a photo if you want — it saves to your own camera roll only.</p>
    </div>

    <div class="btn-row">
      <button class="btn btn-secondary" disabled title="Photo capture isn't wired up yet">Photo</button>
      <button class="btn btn-primary" @click="finish">See this week</button>
    </div>
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area placeholder">
      <p class="eyebrow-accent">Plan</p>
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
const dateLabel = computed(() => new Date().toLocaleDateString('en-AU', { day: 'numeric', month: 'short' }))

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
  router.push('/insights').then(() => missionStore.resetMission())
}
</script>

<style scoped>
.saved-card {
  margin-top: 16px;
  background: var(--card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  padding: 16px 18px;
}

.saved-card .eyebrow-accent { margin-bottom: 6px; }
.saved-line { font-size: 14.5px; line-height: 1.45; color: var(--ink-2); }
.saved-sub { font-size: 12.5px; color: var(--ink-4); margin-top: 4px; }

.photo-note { margin-top: 14px; font-size: 13px; color: var(--ink-4); line-height: 1.5; }

.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; }
</style>
