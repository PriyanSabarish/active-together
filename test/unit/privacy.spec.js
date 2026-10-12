// F68 / V7 — what leaves the phone. Photo checks send the image only; no
// journal data, run_id or location (At home) is in any request; the service
// worker caches no API call, POST body or photo.

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { stripJpegMetadataBytes } from '../../client/src/jpeg'
import { postVerifyStep, postRecommendations, postHomeMissions, postIndoorPlaces, postMissions } from '../../client/src/api'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8')

// SOI, JFIF APP0, EXIF APP1 (with a GPS-looking payload), IPTC APP13, COM, then scan data and EOI.
const seg = (marker, payload) => [0xff, marker, (payload.length + 2) >> 8, (payload.length + 2) & 255, ...payload]
const text = (s) => [...s].map((c) => c.charCodeAt(0))
const WITH_EXIF = Uint8Array.from([
  0xff, 0xd8,
  ...seg(0xe0, text('JFIF\0\x01\x01')),
  ...seg(0xe1, text('Exif\0\0GPSLatitude-37.81 Make iPhone')),
  ...seg(0xed, text('Photoshop 3.0 IPTC')),
  ...seg(0xfe, text('taken at home')),
  0xff, 0xda, 0x00, 0x02, 0x11, 0x22, 0x33, 0xff, 0xd9
])
const asText = (bytes) => String.fromCharCode(...bytes)

describe('JPEG metadata is removed from the bytes that are sent', () => {
  it('drops EXIF, IPTC and comments, and keeps the JFIF header and the image data', () => {
    const out = stripJpegMetadataBytes(WITH_EXIF)
    const s = asText(out)
    expect(s).not.toContain('Exif')
    expect(s).not.toContain('GPSLatitude')
    expect(s).not.toContain('iPhone')
    expect(s).not.toContain('IPTC')
    expect(s).not.toContain('taken at home')
    expect(s).toContain('JFIF')
    expect(out.slice(0, 2)).toEqual(Uint8Array.from([0xff, 0xd8]))
    expect(out.slice(-4)).toEqual(Uint8Array.from([0x22, 0x33, 0xff, 0xd9]))
  })
  it('leaves a clean JPEG and non-JPEG bytes untouched', () => {
    const clean = Uint8Array.from([0xff, 0xd8, ...seg(0xe0, text('JFIF\0')), 0xff, 0xda, 0, 2, 1, 0xff, 0xd9])
    expect(stripJpegMetadataBytes(clean)).toEqual(clean)
    const junk = Uint8Array.from([1, 2, 3, 4, 5, 6])
    expect(stripJpegMetadataBytes(junk)).toBe(junk)
  })
  it('does not guess at a malformed file', () => {
    const bad = Uint8Array.from([0xff, 0xd8, 0xff, 0xe1, 0xff, 0xff, 1, 2])
    expect(stripJpegMetadataBytes(bad)).toBe(bad)
  })
})

describe('requests', () => {
  beforeEach(() => vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) }))))
  afterEach(() => vi.unstubAllGlobals())

  it('a photo check sends the image body with prompt_id and attempt only, and no EXIF', async () => {
    await postVerifyStep({ image: new Blob([WITH_EXIF], { type: 'image/jpeg' }), promptId: 'p_red', attempt: 2 })
    const [url, init] = fetch.mock.calls[0]
    const q = new URL(url).searchParams
    expect([...q.keys()].sort()).toEqual(['attempt', 'prompt_id'])
    expect(init.headers['Content-Type']).toBe('image/jpeg')
    const sent = new Uint8Array(await init.body.arrayBuffer())
    expect(asText(sent)).not.toContain('Exif')
    expect(JSON.stringify(init.headers)).not.toMatch(/run/i)
  })

  it('no request body or query carries a run_id or journal data', async () => {
    await postRecommendations({ latitude: -37.8, longitude: 144.9, radiusKm: 5, durationMin: 60 })
    await postIndoorPlaces({ latitude: -37.8, longitude: 144.9, radiusKm: 5 })
    await postHomeMissions({ durationMin: 20, ageBand: '8-10' })
    await postMissions({ comboId: 'p1', ageBand: '8-10', durationBucket: 40 })
    for (const [url, init] of fetch.mock.calls) {
      expect(String(url) + String(init?.body ?? '')).not.toMatch(/run_?id|photo_id|journal|image_blob/i)
    }
  })

  it('an at-home request carries no location', async () => {
    await postHomeMissions({ durationMin: 15, ageBand: '5-7', recentTemplateIds: [] })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(Object.keys(body).sort()).toEqual(['age_band', 'duration_min', 'recent_template_ids', 'setting'])
  })

  it('indoor-place coordinates are cut to 4 decimal places', async () => {
    await postIndoorPlaces({ latitude: -37.81361234, longitude: 144.96319876, radiusKm: 3 })
    const body = JSON.parse(fetch.mock.calls[0][1].body)
    expect(body.latitude).toBe(-37.8136)
    expect(body.longitude).toBe(144.9632)
  })
})

describe('service worker', () => {
  const config = read('client/vite.config.js')
  it('has no runtime caching, so no API response, POST body or photo is ever cached', () => {
    expect(config).not.toMatch(/runtimeCaching/)
  })
  it('precaches the app shell only, with no photo or blob types', () => {
    const glob = config.match(/globPatterns:\s*\[(.*?)\]/s)[1]
    expect(glob).not.toMatch(/jpe?g|webp|blob|heic/i)
  })
  it('api.js never mentions run_id', () => {
    expect(read('client/src/api.js')).not.toMatch(/run_?id/i)
  })
})
