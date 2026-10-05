import { usePhotoStore } from './photoStore'

// Photos of one outing, for the Week diary, outing detail and You. Real photos
// come from photoStore by runId; demo records carry a colour `tone` instead,
// drawn as a striped placeholder tile.

export const STRIPE = 'repeating-linear-gradient(135deg,rgba(255,255,255,0) 0 9px,rgba(255,255,255,.22) 9px 18px)'

export function usePhotosFor() {
  const photoStore = usePhotoStore()
  return (record) => {
    if (!record) return []
    const real = record.runId ? photoStore.byRun(record.runId) : []
    if (real.length) return real
    return record.tone ? [{ id: `tone-${record.id}`, tone: record.tone, demo: true, stepText: '' }] : []
  }
}

// Background style for a photo tile: the image, or the striped demo tone.
export function tileStyle(photo) {
  if (!photo) return {}
  if (photo.url) return { backgroundImage: `url("${photo.url}")`, backgroundSize: 'cover', backgroundPosition: 'center' }
  return { backgroundColor: photo.tone, backgroundImage: STRIPE }
}

export function longDate(iso) {
  return new Date(iso).toLocaleDateString('en-AU', { weekday: 'short', day: 'numeric', month: 'short' }).replace(',', '')
}
