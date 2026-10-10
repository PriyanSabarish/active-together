<template>
  <template v-if="mission && missionStore.status === 'in_progress'">
    <AppHeader />

    <div class="scroll-area run-scroll">
      <div class="run-head">
        <span class="run-title">{{ mission.title }}</span>
        <button class="run-count" @click="sheet = true">
          Task {{ missionStore.stepIndex + 1 }} of {{ missionStore.totalSteps }}
          <span class="caret">▼</span>
        </button>
      </div>

      <!-- Done = orange, skipped = faded, a photo step still to check = half. -->
      <button class="run-track" aria-label="Show all tasks" @click="sheet = true">
        <span v-for="(bg, i) in dots" :key="i" class="run-seg" :style="{ background: bg }" />
      </button>

      <!-- The one task to read out. Large type on purpose: the phone stays with the parent. -->
      <div class="step-card" :class="{ 'has-photo': showCheckPhoto }">
        <!-- Keepsake camera on every self-confirmed step: never confirms the step. -->
        <button v-if="!isPhotoStep && !keepsake" class="corner-cam" aria-label="Take a photo" @click="openCamera('keep')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="CAMERA" /></svg>
        </button>
        <button v-else-if="!isPhotoStep && keepsake" class="corner-thumb" @click="openCamera('keep')">
          <img :src="keepsake.url" alt="" />
          <span>{{ keepsakeCount === 1 ? '1 photo' : `${keepsakeCount} photos` }}</span>
        </button>

        <div v-if="showCheckPhoto" class="check-photo-wrap">
          <div class="check-photo" :style="{ height: pc === 'retry' ? '150px' : '170px' }">
            <img v-if="checkPhoto" :src="checkPhoto.url" alt="Photo taken for this task" />
            <div v-if="pc === 'checking'" class="checking">
              <span class="spinner" />
              <span>Checking…</span>
            </div>
            <span v-if="pc === 'matched'" class="tick">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
            </span>
            <span v-if="pc === 'offline'" class="kept">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="3" width="10" height="18" rx="2.5" /><path d="M11 17.5h2" /></svg>
              Kept on this phone
            </span>
          </div>
          <div v-if="pc === 'retry'" class="attempts">
            <span v-for="i in 2" :key="i" :class="{ used: i <= tries }" />
          </div>
        </div>

        <div v-else class="sketch" aria-hidden="true">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path :d="taskIcon(step.icon)" /></svg>
        </div>

        <span v-if="isPhotoStep && pc === 'idle'" class="pc-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path :d="CAMERA" /></svg>
          Photo check
        </span>
        <h1 class="step-big" :style="{ fontSize: view.size }">{{ view.head }}</h1>
        <p class="step-hint" :class="{ tight: showCheckPhoto }">{{ view.hint }}</p>
      </div>

      <button class="btn btn-accent primary" :style="{ opacity: view.dim ? 0.35 : 1 }" @click="view.go">
        <svg v-if="view.cam" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path :d="CAMERA" /></svg>
        {{ view.label }}
      </button>
      <button v-for="b in view.sec" :key="b.label" class="btn secondary" @click="b.go">{{ b.label }}</button>

      <!-- Giving up ends the mission without a history record (AC-8.1.4); the note is the warning. -->
      <button class="giveup" @click="abandon">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 6l-6 6 6 6 M4.5 12h14" /></svg>
        Give up this mission
      </button>
      <p class="offline-note">
        Nothing is logged if you stop now.<template v-if="runPhotoCount"> Photos from this mission won't be kept.</template>
      </p>
    </div>

    <!-- All tasks: jump to any one. -->
    <div v-if="sheet" class="sheet-scrim" @click="sheet = false">
      <div class="sheet" @click.stop>
        <span class="grabber" />
        <div class="sheet-head">
          <span class="sheet-title">{{ mission.title }}</span>
          <button class="sheet-close" @click="sheet = false">Close</button>
        </div>
        <button v-for="row in sheetRows" :key="row.num" class="sheet-row" :class="row.state" @click="jumpTo(row.num - 1)">
          <span class="mark">
            <svg v-if="row.state === 'done'" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
            <span v-else-if="row.state === 'skipped'" class="dash" />
            <span v-else-if="row.state === 'current'" class="dot" />
            <span v-else class="num">{{ row.num }}</span>
          </span>
          <span class="row-text">
            <span class="row-title">{{ row.text }}</span>
            <span class="row-status">{{ row.status }}</span>
          </span>
          <img v-if="row.thumb" class="row-thumb" :src="row.thumb" alt="" />
          <svg v-else-if="row.cam" class="row-cam" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="CAMERA" /></svg>
        </button>
      </div>
    </div>

    <!-- Camera: live viewfinder with the task and privacy note. -->
    <CameraOverlay
      v-if="camera"
      :prompt="step.title.replace(/\.$/, '')"
      :note="camera === 'keep' ? 'Just a keepsake. Stays on this phone.' : 'Checked once, then deleted from the server. A copy stays on this phone.'"
      @capture="onCapture"
      @cancel="camera = null"
      @error="onCaptureError"
    />
  </template>

  <template v-else>
    <AppHeader />
    <div class="scroll-area placeholder">
      <p class="eyebrow-accent">Play</p>
      <h1>No mission running</h1>
      <p class="subtitle">Pick a place on Play, then start a mission from there.</p>
      <button class="btn btn-outline" style="margin-top: 16px" @click="router.push('/play')">Go to Play</button>
    </div>
  </template>
</template>

<script setup>
// Mission in progress, on the dark shell (route.meta.dark). One task at a
// time in large type; Done and Skip both advance (nothing is a fail).
//
// Photo-check steps (confirm 'photo', story 6.3): take a photo, it is checked
// once; a miss offers two more tries, then a tap confirm. Offline or no scorer
// goes straight to a tap confirm. Every other step has a corner camera for a
// keepsake that never confirms the step (story 10.3). Photos are linked to
// this run by runId and dropped if the mission is given up (D11).

import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import CameraOverlay from '../components/CameraOverlay.vue'
import { useMissionStore } from '../missionStore'
import { usePhotoStore } from '../photoStore'
import { postVerifyStep } from '../api'
import { taskIcon, CAMERA } from '../taskIcons'

const ORANGE = '#E8913A'
const OFF = 'rgba(242,241,236,.22)'

const router = useRouter()
const missionStore = useMissionStore()
const photoStore = usePhotoStore()
const mission = computed(() => missionStore.active)
const step = computed(() => missionStore.currentStep)
const isLast = computed(() => missionStore.stepIndex === missionStore.totalSteps - 1)
const isPhotoStep = computed(() => step.value?.confirm === 'photo')

const sheet = ref(false)
const camera = ref(null) // null | 'keep' | 'check'
const pc = ref('idle') // idle | checking | matched | retry | fallback | offline
const tries = ref(0)
const checkedBy = ref('')
let checkToken = 0

watch(() => missionStore.stepIndex, () => {
  pc.value = 'idle'
  tries.value = 0
  checkedBy.value = ''
  camera.value = null
  checkToken += 1
})

const runPhotos = computed(() => photoStore.byRun(missionStore.runId))
const runPhotoCount = computed(() => runPhotos.value.length)
const stepPhotos = (i, source) => runPhotos.value.filter((p) => p.stepIndex === i && (!source || p.source === source))
const keepsakes = computed(() => stepPhotos(missionStore.stepIndex, 'mission'))
const keepsake = computed(() => keepsakes.value[keepsakes.value.length - 1] ?? null)
const keepsakeCount = computed(() => keepsakes.value.length)
const checkPhoto = computed(() => {
  const list = stepPhotos(missionStore.stepIndex, 'check')
  return list[list.length - 1] ?? null
})
const showCheckPhoto = computed(() => isPhotoStep.value && pc.value !== 'idle')

const dots = computed(() => mission.value.steps.map((_, i) => {
  const r = missionStore.results[i]
  if (i === missionStore.stepIndex) {
    return isPhotoStep.value && pc.value !== 'matched' ? `linear-gradient(90deg,${ORANGE} 50%,${OFF} 50%)` : ORANGE
  }
  if (r === 'done') return ORANGE
  if (r === 'skipped') return 'rgba(242,241,236,.4)'
  return OFF
}))

const sheetRows = computed(() => mission.value.steps.map((s, i) => {
  const state = i === missionStore.stepIndex ? 'current' : missionStore.results[i] || 'todo'
  const last = stepPhotos(i).at(-1)
  return {
    num: i + 1,
    text: s.title,
    state,
    status: { done: 'Done', skipped: 'Skipped', current: 'Now', todo: 'To do' }[state],
    cam: s.confirm === 'photo',
    thumb: last?.url ?? ''
  }
}))

function done() { advance('done') }
function skip() { advance('skipped') }
const skipBtn = { label: 'Skip this one', go: skip }

// What the card and buttons say, per photo-check state.
const view = computed(() => {
  const head = step.value.title
  if (!isPhotoStep.value) {
    return { head, hint: isLast.value ? 'Last one. Then head back.' : 'Read it out. No rush.', label: isLast.value ? 'Finish mission' : 'Done', go: done, sec: [skipBtn] }
  }
  const finishLabel = isLast.value ? 'Finish mission' : 'Next task  →'
  switch (pc.value) {
    case 'checking':
      return { head, hint: 'This only takes a moment.', label: 'Take photo', cam: true, dim: true, go: () => {}, sec: [skipBtn] }
    case 'matched':
      return { head: 'Got it!', size: '34px', hint: `Saved to today’s outing.${checkedBy.value ? ` Checked by ${checkedBy.value}.` : ''}`, label: finishLabel, go: done, sec: [] }
    case 'retry':
      return { head: 'Hmm, let’s try another angle.', size: '27px', hint: 'Get a bit closer, in good light.', label: 'Try again', cam: true, go: () => openCamera('check'), sec: [{ label: 'It’s done — tick it off', go: done }, skipBtn] }
    case 'fallback':
      return { head: 'Tricky one! You can tick it off yourself.', size: '28px', hint: 'The photo’s kept for the outing journal.', label: 'Done', go: done, sec: [skipBtn] }
    case 'offline':
      return { head: 'Can’t check right now — tick it off if they found it.', size: '26px', hint: 'Your photo is safe.', label: 'Done', go: done, sec: [skipBtn] }
    default:
      return { head, hint: 'Read it out. Snap it when they find it.', label: 'Take photo', cam: true, go: () => openCamera('check'), sec: [skipBtn] }
  }
})

function openCamera(kind) {
  camera.value = kind
}

// Could not read the photo: keep nothing and never upload anything.
function onCaptureError() {
  const kind = camera.value
  camera.value = null
  if (kind === 'check') pc.value = 'offline'
}

// blob is already a clean JPEG (CameraOverlay redraws it through a canvas).
async function onCapture(blob) {
  const kind = camera.value
  camera.value = null
  if (!kind) return

  const stepIndex = missionStore.stepIndex
  const base = { runId: missionStore.runId, blob, stepIndex, stepText: step.value.title }
  if (kind === 'keep') {
    photoStore.addPhoto({ ...base, source: 'mission' })
    return
  }

  // A new check photo replaces the previous attempt for this step.
  stepPhotos(stepIndex, 'check').forEach((p) => photoStore.removePhoto(p.id, { undoable: false }))
  photoStore.addPhoto({ ...base, source: 'check' })
  tries.value += 1
  pc.value = 'checking'
  const token = ++checkToken
  try {
    const res = await postVerifyStep({ image: blob, promptId: step.value.promptId, attempt: tries.value })
    if (token !== checkToken) return
    checkedBy.value = res?.checked_by ?? ''
    if (res?.result === 'confirmed' || res?.result === 'match') pc.value = 'matched'
    else if (tries.value >= 3 || res?.result === 'use_tap' || res?.attempts_left === 0) pc.value = 'fallback'
    else pc.value = 'retry'
  } catch {
    if (token === checkToken) pc.value = 'offline'
  }
}

function jumpTo(i) {
  sheet.value = false
  missionStore.goToStep(i)
}

function abandon() {
  photoStore.removeRun(missionStore.runId)
  missionStore.abandonMission()
  router.push('/play')
}

function advance(result) {
  missionStore.completeStep(result)
  if (missionStore.status === 'done') router.push('/play/finished')
}
</script>

<style scoped>
.run-scroll { display: flex; flex-direction: column; }

.run-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.run-title { font-size: 13.5px; font-weight: 600; color: rgba(242, 241, 236, 0.6); flex: 1; min-width: 0; }

.run-count {
  background: none;
  border: none;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--accent);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.caret { font-size: 10px; opacity: 0.75; }

.run-track {
  display: flex;
  gap: 4px;
  margin: 4px 0 10px;
  padding: 6px 0;
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
}

.run-seg { flex: 1; height: 5px; border-radius: 999px; }

.step-card {
  position: relative;
  border-radius: 24px;
  background: rgba(242, 241, 236, 0.06);
  box-shadow: inset 0 0 0 1px rgba(242, 241, 236, 0.14);
  padding: 22px 24px 26px;
  margin-bottom: 20px;
}

.step-card.has-photo { padding: 18px 18px 24px; }

.corner-cam,
.corner-thumb {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 1;
  height: 44px;
  border: none;
  border-radius: 999px;
  background: rgba(242, 241, 236, 0.1);
  box-shadow: inset 0 0 0 1px rgba(242, 241, 236, 0.2);
  color: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: inherit;
}

.corner-cam { width: 44px; }
.corner-cam:active { transform: scale(0.94); }
.corner-thumb { gap: 8px; padding: 0 12px 0 5px; font-size: 12.5px; font-weight: 600; }
.corner-thumb img { width: 34px; height: 34px; border-radius: 50%; object-fit: cover; }

.check-photo-wrap { margin-bottom: 16px; }

.check-photo {
  position: relative;
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(165deg, #9FB08C 0%, #C9CDB1 55%, #A3B191 100%);
}

.check-photo img { width: 100%; height: 100%; object-fit: cover; display: block; }

.checking {
  position: absolute;
  inset: 0;
  background: rgba(30, 42, 31, 0.55);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--paper);
}

.spinner {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 3px solid rgba(242, 241, 236, 0.25);
  border-top-color: var(--paper);
  animation: spin 0.9s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.tick {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #3F8F47;
  box-shadow: 0 0 0 3px rgba(30, 42, 31, 0.6);
  color: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kept {
  position: absolute;
  left: 10px;
  bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 11px 0 9px;
  border-radius: 999px;
  background: rgba(14, 20, 15, 0.72);
  font-size: 12px;
  font-weight: 600;
  color: var(--paper);
}

.attempts { display: flex; justify-content: center; gap: 7px; padding-top: 11px; }
.attempts span { width: 7px; height: 7px; border-radius: 50%; background: rgba(242, 241, 236, 0.2); }
.attempts span.used { background: rgba(242, 241, 236, 0.75); }

.sketch {
  height: 132px;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(242, 241, 236, 0.55);
}

.pc-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px 0 10px;
  margin-bottom: 12px;
  border-radius: 999px;
  background: rgba(232, 145, 58, 0.16);
  color: #F0A55C;
  font-size: 12.5px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.step-big {
  color: var(--paper);
  font-size: 30px;
  line-height: 1.15;
  letter-spacing: -0.7px;
  margin: 0;
  text-wrap: pretty;
}

.step-hint { margin-top: 16px; font-size: 14.5px; line-height: 1.4; color: rgba(242, 241, 236, 0.55); }
.step-hint.tight { margin-top: 10px; }

.primary { width: 100%; border-radius: 999px; font-weight: 700; box-shadow: none; }

.secondary {
  margin-top: 10px;
  width: 100%;
  height: 50px;
  border-radius: 999px;
  background: transparent;
  color: rgba(242, 241, 236, 0.8);
  border: none;
  box-shadow: inset 0 0 0 1px rgba(242, 241, 236, 0.22);
  font-size: 15.5px;
}

.giveup {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 44px;
  margin-top: 10px;
  background: none;
  border: none;
  color: var(--paper);
  font-size: 14.5px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
}

/* Short screens (a phone with browser bars): a smaller sketch and card, so
   the task and its buttons fit; anything left over scrolls. */
@media (max-height: 760px) {
  .sketch { height: 72px; margin-bottom: 10px; }
  .sketch svg { width: 52px; height: 52px; }
  .step-card { padding: 18px 20px 20px; margin-bottom: 14px; }
  .step-big { font-size: 26px; }
  .step-hint { margin-top: 10px; }
  .run-track { margin-bottom: 6px; }
}

/* Hover only where there is a pointer: on a phone a tap leaves :hover stuck. */
@media (hover: hover) {
  .giveup:hover { color: var(--accent); }
}

.offline-note { text-align: center; font-size: 12.5px; color: rgba(242, 241, 236, 0.72); line-height: 1.4; padding-top: 2px; }

/* ---- task sheet ---- */
.sheet-scrim {
  position: absolute;
  inset: 0;
  z-index: 8;
  background: rgba(10, 14, 11, 0.62);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.sheet {
  background: #253326;
  border-radius: 28px 28px 0 0;
  box-shadow: inset 0 1px 0 rgba(242, 241, 236, 0.12);
  padding: 10px 16px 38px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.grabber { width: 40px; height: 5px; border-radius: 999px; background: rgba(242, 241, 236, 0.25); margin: 0 auto 12px; }

.sheet-head { display: flex; align-items: baseline; justify-content: space-between; padding: 0 8px 8px; }
.sheet-title { font-family: var(--font-display); font-weight: 600; font-size: 21px; letter-spacing: -0.4px; color: var(--paper); }
.sheet-close { background: none; border: none; font-family: inherit; font-size: 15px; font-weight: 600; color: var(--accent); cursor: pointer; padding: 8px 0; }

.sheet-row {
  display: flex;
  align-items: center;
  gap: 13px;
  min-height: 60px;
  padding: 8px 12px;
  border: none;
  border-radius: 16px;
  background: transparent;
  font-family: inherit;
  text-align: left;
  color: var(--paper);
  cursor: pointer;
}

.sheet-row.current { background: rgba(232, 145, 58, 0.12); }

.mark {
  width: 28px;
  height: 28px;
  flex: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1.5px rgba(242, 241, 236, 0.25);
}

.sheet-row.done .mark { background: var(--accent); box-shadow: none; color: var(--dark); }
.sheet-row.current .mark { box-shadow: inset 0 0 0 1.5px var(--accent); }
.mark .dash { width: 11px; height: 2.5px; border-radius: 2px; background: rgba(242, 241, 236, 0.6); }
.mark .dot { width: 11px; height: 11px; border-radius: 50%; background: var(--accent); }
.mark .num { font-size: 12px; font-weight: 700; color: rgba(242, 241, 236, 0.55); }

.row-text { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.row-title { font-size: 15px; line-height: 1.35; font-weight: 600; }
.sheet-row.skipped .row-title { color: rgba(242, 241, 236, 0.6); }
.row-status { margin-top: 2px; font-size: 12.5px; color: rgba(242, 241, 236, 0.5); }
.row-cam { flex: none; color: rgba(242, 241, 236, 0.55); }
.row-thumb { width: 36px; height: 36px; flex: none; border-radius: 10px; object-fit: cover; }

.placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 8px;
}

.placeholder h1 { margin-top: 4px; color: var(--paper); }
</style>
