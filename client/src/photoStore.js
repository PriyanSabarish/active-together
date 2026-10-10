import { defineStore } from 'pinia'
import { PHOTOS, getAll, put, remove, removeByRun, askPersist } from './db'

// ---------------------------------------------------------------------------
// Mission photos (story 10.3 / 10.4), saved on the device in IndexedDB
// (db.js, store journey_photo) and never sent anywhere — the photo-check
// upload is a separate copy made by the run screen.
//
// Every photo is tied to its outing by runId (created when a mission starts,
// never sent to the server). A photo is written as soon as it is taken; one
// whose run never became a record (the app closed mid-mission) is dropped by
// hydrate() on the next start, the same as an abandoned run (D11).
//
// source: 'mission' (keepsake taken on any step), 'check' (photo-check image,
// kept in the journal) or 'end' (end-of-mission photo).
// ---------------------------------------------------------------------------

let seq = 0

// What is written to IndexedDB: everything but the page-local object URL.
function toRow(photo) {
  const { url, ...row } = photo
  return row
}

function revoke(photo) {
  if (photo?.url && typeof URL !== 'undefined' && URL.revokeObjectURL) {
    try { URL.revokeObjectURL(photo.url) } catch { /* not an object URL */ }
  }
}

export const usePhotoStore = defineStore('photos', {
  state: () => ({
    photos: [], // { id, runId, stepIndex, stepText, source, url, capturedAt, blob }
    toast: null, // { text, undo?: () => void }
    _toastTimer: null,
    _pendingRevoke: null // photo removed but still undoable
  }),
  getters: {
    byRun(state) {
      return (runId) => state.photos.filter((p) => p.runId === runId)
    },
    countForRun(state) {
      return (runId) => state.photos.filter((p) => p.runId === runId).length
    },
    hasStepPhoto(state) {
      return (runId, stepIndex) => state.photos.some((p) => p.runId === runId && p.stepIndex === stepIndex)
    }
  },
  actions: {
    // Load saved photos at startup. keepRuns is the set of runIds that have a
    // record (plus any run in progress); every other saved photo is an orphan
    // from a run that never finished and is deleted.
    async hydrate(keepRuns) {
      const saved = await getAll(PHOTOS)
      const have = new Set(this.photos.map((p) => p.id))
      for (const row of saved) {
        if (have.has(row.id)) continue
        if (!keepRuns.has(row.runId)) {
          remove(PHOTOS, row.id)
          continue
        }
        const { blob, ...meta } = row
        this.photos.push({ ...meta, blob, url: blob ? URL.createObjectURL(blob) : '' })
      }
      this.photos.sort((a, b) => a.capturedAt.localeCompare(b.capturedAt))
    },
    addPhoto({ runId, blob, url, stepIndex = null, stepText = '', source = 'mission' }) {
      seq += 1
      const photo = {
        id: `ph-${Date.now()}-${seq}`,
        runId,
        stepIndex,
        stepText,
        source,
        url: url ?? (blob ? URL.createObjectURL(blob) : ''),
        capturedAt: new Date().toISOString(),
        blob: blob ?? null
      }
      this.photos.push(photo)
      if (blob) {
        askPersist()
        put(PHOTOS, toRow(photo))
      }
      return photo
    },
    // Delete one photo with a short undo window; the record stays (D15).
    removePhoto(id, { undoable = true } = {}) {
      const idx = this.photos.findIndex((p) => p.id === id)
      if (idx === -1) return
      const [photo] = this.photos.splice(idx, 1)
      remove(PHOTOS, photo.id)
      if (!undoable) return revoke(photo)
      this.finishPendingRevoke()
      this._pendingRevoke = photo
      this.flash('Photo deleted', () => {
        this.photos.splice(Math.min(idx, this.photos.length), 0, photo)
        if (photo.blob) put(PHOTOS, toRow(photo))
        this._pendingRevoke = null
      })
    },
    // Abandoned run (D11) or deleted record (D15): every photo of that run goes.
    removeRun(runId) {
      if (!runId) return
      this.photos.filter((p) => p.runId === runId).forEach(revoke)
      this.photos = this.photos.filter((p) => p.runId !== runId)
      removeByRun(runId)
    },
    flash(text, undo = null) {
      clearTimeout(this._toastTimer)
      this.toast = { text, undo }
      this._toastTimer = setTimeout(() => this.dismissToast(), 4000)
    },
    undoToast() {
      const undo = this.toast?.undo
      clearTimeout(this._toastTimer)
      this.toast = null
      if (undo) undo()
    },
    dismissToast() {
      clearTimeout(this._toastTimer)
      this.toast = null
      this.finishPendingRevoke()
    },
    finishPendingRevoke() {
      if (this._pendingRevoke) revoke(this._pendingRevoke)
      this._pendingRevoke = null
    }
  }
})

// Resize to ~1080 px on the long edge and re-encode as JPEG. Drawing through a
// canvas drops every EXIF tag (GPS included) before the image is kept or sent.
export async function toCleanJpeg(file, maxEdge = 1080) {
  const bitmap = await loadBitmap(file)
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height))
  const w = Math.round(bitmap.width * scale)
  const h = Math.round(bitmap.height * scale)
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  canvas.getContext('2d').drawImage(bitmap, 0, 0, w, h)
  bitmap.close?.()
  return new Promise((resolve, reject) => {
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('Could not encode photo'))), 'image/jpeg', 0.85)
  })
}

async function loadBitmap(file) {
  if (typeof createImageBitmap === 'function') {
    // Applies the EXIF orientation, so the pixels come out the right way up.
    return createImageBitmap(file, { imageOrientation: 'from-image' })
  }
  const url = URL.createObjectURL(file)
  try {
    const img = new Image()
    img.src = url
    await img.decode()
    return img
  } finally {
    URL.revokeObjectURL(url)
  }
}
