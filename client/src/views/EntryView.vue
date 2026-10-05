<template>
  <AppHeader />
  <div class="scroll-area">
    <button class="back" aria-label="Back" @click="back">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M19.5 12h-14 M11.5 6l-6 6 6 6" /></svg>
    </button>

    <template v-if="record">
      <div v-if="current" class="hero" :style="tileStyle(current)">
        <span v-if="current.stepText" class="caption">{{ current.stepText }}</span>
      </div>
      <div v-else class="hero empty-hero">
        <svg width="84" height="84" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path :d="categoryIcon(record.category)" /></svg>
      </div>

      <!-- More than one photo: pick which one the buttons act on. -->
      <div v-if="photos.length > 1" class="thumbs">
        <button v-for="(p, i) in photos" :key="p.id" class="thumb" :class="{ on: i === selected }" :style="tileStyle(p)" :aria-label="p.stepText || `Photo ${i + 1}`" @click="selected = i" />
      </div>

      <h1 class="name">{{ record.missionTitle }}</h1>
      <p class="sub">{{ record.placeName }} · {{ longDate(record.date) }} · {{ record.durationMin }} min</p>

      <div v-if="record.feedback" class="fb">
        <span class="fb-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path :d="FEEDBACK_ICON[record.feedback]" /></svg>
        </span>
        <span class="fb-label">{{ feedbackLabel(record.feedback) }}</span>
      </div>

      <div v-if="current" class="actions">
        <button v-if="!current.demo" class="btn btn-primary save" @click="savePhoto">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11 M7 10.5l5 5 5-5 M5 20h14" /></svg>
          Save to Photos
        </button>
        <button class="del-photo" @click="deletePhoto">Delete photo</button>
      </div>

      <p class="note">Photos stay on this phone. Clearing your browser data removes them.</p>
      <button class="del-record" @click="deleteRecord">Delete this outing</button>
    </template>

    <template v-else>
      <h1 class="name">Outing not found</h1>
      <p class="sub">It may have been deleted.</p>
    </template>
  </div>
</template>

<script setup>
// One outing (story 10.4): its photo, or the place icon when there is none,
// mission name, place, date, length and the child's feedback. Save to Photos
// hands the image to the share sheet (or a download); Delete photo keeps the
// record (D15), with a short undo. Deleting the outing deletes its photos.

import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { useHistoryStore, feedbackLabel } from '../historyStore'
import { usePhotoStore } from '../photoStore'
import { usePhotosFor, tileStyle, longDate } from '../journal'
import { categoryIcon, FEEDBACK_ICON } from '../taskIcons'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()
const historyStore = useHistoryStore()
const photoStore = usePhotoStore()
const photosFor = usePhotosFor()

const record = computed(() => historyStore.records.find((r) => r.id === props.id) ?? null)
const photos = computed(() => photosFor(record.value))
const selected = ref(0)
const current = computed(() => photos.value[selected.value] ?? photos.value[0] ?? null)

watch(() => photos.value.length, (n) => { if (selected.value >= n) selected.value = Math.max(0, n - 1) })

function back() {
  if (window.history.length > 1) router.back()
  else router.push('/week')
}

async function savePhoto() {
  const p = current.value
  if (!p?.url) return
  const name = `active-together-${record.value.date}.jpg`
  try {
    const blob = await (await fetch(p.url)).blob()
    const file = new File([blob], name, { type: 'image/jpeg' })
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file] })
      return
    }
  } catch (e) {
    if (e?.name === 'AbortError') return // share sheet dismissed
  }
  const a = document.createElement('a')
  a.href = p.url
  a.download = name
  a.click()
  photoStore.flash('Saved to Photos')
}

function deletePhoto() {
  const p = current.value
  if (!p) return
  if (p.demo) {
    // Demo placeholder: clear the tone, undo puts it back.
    const r = record.value
    const tone = r.tone
    r.tone = null
    photoStore.flash('Photo deleted', () => { r.tone = tone })
    return
  }
  photoStore.removePhoto(p.id)
}

function deleteRecord() {
  const r = record.value
  if (!r) return
  photoStore.removeRun(r.runId)
  historyStore.removeRecord(r.id)
  router.push('/week')
}
</script>

<style scoped>
.back {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: var(--tint);
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 14px;
}

.hero {
  position: relative;
  margin: 0 -24px;
  aspect-ratio: 4 / 3;
  background-color: #BFD4B0;
}

.empty-hero {
  background: rgba(47, 107, 54, 0.1);
  color: var(--green);
  display: flex;
  align-items: center;
  justify-content: center;
}

.caption {
  position: absolute;
  left: 14px;
  bottom: 12px;
  max-width: calc(100% - 28px);
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(14, 20, 15, 0.6);
  font-size: 12px;
  font-weight: 600;
  color: var(--paper);
}

.thumbs { display: flex; gap: 8px; margin-top: 12px; overflow-x: auto; }
.thumb { width: 56px; height: 56px; flex: none; border: none; border-radius: 12px; cursor: pointer; opacity: 0.6; }
.thumb.on { opacity: 1; box-shadow: 0 0 0 2px var(--paper), 0 0 0 4px var(--green); }

.name { margin: 20px 0 4px; font-size: 27px; line-height: 1.1; }
.sub { font-size: 14px; color: rgba(30, 42, 31, 0.55); }

.fb { display: flex; align-items: center; gap: 9px; margin-top: 14px; }
.fb-icon { width: 32px; height: 32px; border-radius: 50%; background: var(--tint); color: rgba(30, 42, 31, 0.6); display: flex; align-items: center; justify-content: center; }
.fb-label { font-size: 14.5px; font-weight: 600; }

.actions { display: flex; flex-direction: column; gap: 6px; margin-top: 26px; }
.save { width: 100%; border-radius: 999px; }

.del-photo,
.del-record {
  height: 48px;
  background: none;
  border: none;
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  color: rgba(30, 42, 31, 0.55);
  cursor: pointer;
}

.note { margin: 22px 4px 0; font-size: 12.5px; line-height: 1.5; color: var(--ink-4); text-align: center; text-wrap: pretty; }
.del-record { display: block; margin: 8px auto 0; font-size: 13.5px; color: var(--danger); }
</style>
