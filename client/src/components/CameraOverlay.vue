<template>
  <div class="camera">
    <!-- Live viewfinder; until it starts (or if it can't) the design's gradient shows. -->
    <video v-show="live" ref="videoEl" class="feed" autoplay playsinline muted />
    <div class="shade" />

    <div class="cam-prompt">{{ prompt }}</div>
    <div class="cam-frame">
      <span v-if="state === 'starting'" class="cam-status">Starting camera…</span>
      <span v-else-if="state === 'fallback'" class="cam-status">Camera not available here. Tap the button to pick a photo instead.</span>
    </div>
    <p class="cam-note">{{ note }}</p>
    <div class="cam-controls">
      <button class="cam-cancel" @click="emit('cancel')">Cancel</button>
      <button class="shutter" :aria-label="live ? 'Take photo' : 'Pick a photo'" :disabled="state === 'starting' || busy" @click="shoot"><span /></button>
      <span />
    </div>
    <input ref="fileInput" class="file-input" type="file" accept="image/*" capture="environment" @change="onFile" />
  </div>
</template>

<script setup>
// Full-screen camera used by the mission run (step and photo-check photos) and
// the end-of-mission prompt. Shows the back camera live through getUserMedia
// and grabs a frame on the shutter. If the camera can't be opened (no camera,
// permission refused, not https), the shutter falls back to the phone's own
// picker. Either way the photo is redrawn through a canvas, so what comes out
// is a ~1080 px JPEG with no EXIF or GPS.
//
// emits: capture(blob) — clean JPEG; cancel; error — the photo couldn't be read.

import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { toCleanJpeg } from '../photoStore'

defineProps({
  prompt: { type: String, required: true },
  note: { type: String, default: '' }
})
const emit = defineEmits(['capture', 'cancel', 'error'])

const videoEl = ref(null)
const fileInput = ref(null)
const state = ref('starting') // starting | live | fallback
const busy = ref(false)
const live = computed(() => state.value === 'live')
let stream = null
let closed = false

onMounted(async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    state.value = 'fallback'
    return
  }
  try {
    const s = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1440 } },
      audio: false
    })
    if (closed) return s.getTracks().forEach((t) => t.stop())
    stream = s
    videoEl.value.srcObject = s
    await videoEl.value.play().catch(() => {})
    state.value = 'live'
  } catch {
    state.value = 'fallback'
  }
})

onBeforeUnmount(() => {
  closed = true
  stream?.getTracks().forEach((t) => t.stop())
})

async function shoot() {
  if (!live.value) return fileInput.value.click()
  const v = videoEl.value
  if (!v.videoWidth) return
  busy.value = true
  try {
    const scale = Math.min(1, 1080 / Math.max(v.videoWidth, v.videoHeight))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(v.videoWidth * scale)
    canvas.height = Math.round(v.videoHeight * scale)
    canvas.getContext('2d').drawImage(v, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85))
    if (blob) emit('capture', blob)
    else emit('error')
  } finally {
    busy.value = false
  }
}

async function onFile(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  try {
    emit('capture', await toCleanJpeg(file))
  } catch {
    emit('error')
  }
}
</script>

<style scoped>
.camera {
  position: absolute;
  inset: 0;
  z-index: 9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(170deg, #7E8F72 0%, #A9B596 38%, #C7C9AE 60%, #8D9A7A 100%);
}

.feed { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; background: #0E140F; }

.shade {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(14, 20, 15, 0.55) 0%, rgba(14, 20, 15, 0) 22%, rgba(14, 20, 15, 0) 66%, rgba(14, 20, 15, 0.8) 100%);
}

.cam-prompt,
.cam-frame,
.cam-note,
.cam-controls { position: relative; }

.cam-prompt {
  align-self: center;
  margin: 66px 22px 0;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(14, 20, 15, 0.78);
  color: var(--paper);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
  text-align: center;
}

.cam-frame {
  flex: 1;
  margin: 22px 30px 26px;
  border-radius: 30px;
  box-shadow: inset 0 0 0 1.5px rgba(242, 241, 236, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.cam-status { max-width: 240px; text-align: center; font-size: 14px; line-height: 1.45; font-weight: 600; color: var(--paper); text-shadow: 0 1px 6px rgba(14, 20, 15, 0.5); }
.cam-note { padding: 0 30px; text-align: center; font-size: 13px; line-height: 1.45; color: rgba(242, 241, 236, 0.78); }

.cam-controls { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 20px 26px 44px; }
.cam-cancel { justify-self: start; height: 48px; background: none; border: none; font-family: inherit; font-size: 16px; font-weight: 600; color: var(--paper); cursor: pointer; }

.shutter {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: none;
  background: transparent;
  box-shadow: inset 0 0 0 4px var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.shutter span { width: 64px; height: 64px; border-radius: 50%; background: var(--paper); }
.shutter:active { transform: scale(0.94); }
.shutter:disabled { opacity: 0.5; cursor: default; transform: none; }

.file-input { display: none; }
</style>
