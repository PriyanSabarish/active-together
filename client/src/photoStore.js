import { defineStore } from 'pinia'

// ---------------------------------------------------------------------------
// Mission photos (story 10.3 / 10.4), held in memory for this iteration.
//
// Every photo is tied to its outing by runId (created when a mission starts,
// never sent to the server). Nothing here is written to IndexedDB yet, so a
// reload drops the photos — the device store (F55) swaps in underneath this
// API later without the screens changing.
//
// source: 'mission' (keepsake taken on any step), 'check' (photo-check image,
// kept in the journal) or 'end' (end-of-mission photo).
// ---------------------------------------------------------------------------

let seq = 0

function revoke(photo) {
  if (photo?.url && typeof URL !== 'undefined' && URL.revokeObjectURL) {
    try { URL.revokeObjectURL(photo.url) } catch { /* not an object URL */ }
  }
}

export const usePhotoStore = defineStore('photos', {
  state: () => ({
    photos: [], // { id, runId, stepIndex, stepText, source, url, capturedAt }
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
    addPhoto({ runId, blob, url, stepIndex = null, stepText = '', source = 'mission' }) {
      seq += 1
      const photo = {
        id: `ph-${Date.now()}-${seq}`,
        runId,
        stepIndex,
        stepText,
        source,
        url: url ?? (blob ? URL.createObjectURL(blob) : ''),
        capturedAt: new Date().toISOString()
      }
      this.photos.push(photo)
      return photo
    },
    // Delete one photo with a short undo window; the record stays (D15).
    removePhoto(id, { undoable = true } = {}) {
      const idx = this.photos.findIndex((p) => p.id === id)
      if (idx === -1) return
      const [photo] = this.photos.splice(idx, 1)
      if (!undoable) return revoke(photo)
      this.finishPendingRevoke()
      this._pendingRevoke = photo
      this.flash('Photo deleted', () => {
        this.photos.splice(Math.min(idx, this.photos.length), 0, photo)
        this._pendingRevoke = null
      })
    },
    // Abandoned run (D11) or deleted record (D15): every photo of that run goes.
    removeRun(runId) {
      if (!runId) return
      this.photos.filter((p) => p.runId === runId).forEach(revoke)
      this.photos = this.photos.filter((p) => p.runId !== runId)
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
