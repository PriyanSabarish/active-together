// Thin client for the FastAPI backend (server/app/main.py).
//
// Base URL of the backend. Defaults to the deployed Render service so a fresh
// clone runs with no configuration. Override with VITE_API_BASE_URL in
// client/.env (e.g. http://localhost:8000 for a local backend).

const DEFAULT_BASE_URL = 'https://active-together.onrender.com'
const BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function messageFor(status, detail) {
  if (status === 503) return 'The places dataset is temporarily unavailable. Please try again shortly.'
  if (status === 400 || status === 422) return typeof detail === 'string' ? detail : 'The search request was invalid.'
  return 'The Active Together service returned an error. Please try again.'
}

async function request(path, init = {}) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...(init.headers ?? {}) }
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new ApiError('Could not reach the Active Together service. Check your connection and try again.', 0)
  }

  if (!res.ok) {
    let detail = null
    try {
      detail = (await res.json())?.detail ?? null
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(messageFor(res.status, detail), res.status, detail)
  }

  return res.json()
}

// POST /recommendations
// body: { latitude, longitude, radius_km, duration_min, travel_mode, excluded_categories }
// duration_min is the WHOLE outing in minutes (travel out + play + travel back), 20-120.
// returns: { status: 'ok' | 'zero_results' | 'out_of_bounds', combos: [...], message?,
//            suggest_indoors, suggestions?: [{ kind: 'more_time', total_min, fits_count } | { kind: 'other_mode', mode }] }
// Each combo has its own plan length (duration_bucket) and a travel block.
export function postRecommendations({ latitude, longitude, radiusKm, durationMin, travelMode = 'walking', excludedCategories = [] }) {
  return request('/recommendations', {
    method: 'POST',
    body: JSON.stringify({
      latitude,
      longitude,
      radius_km: radiusKm,
      duration_min: durationMin,
      travel_mode: travelMode,
      excluded_categories: excludedCategories
    })
  })
}

// GET /data/context?lat=&lon=
// returns the current readings for a point:
// { available, temp_c, precip_prob, wind_gust_kmh, uv_index, pm25, pm10 }
// Since Oct 2026 the backend wraps them as { status, context: {...} }; both
// shapes are accepted so callers always get the flat readings.
export async function getContext({ latitude, longitude }) {
  const qs = new URLSearchParams({ lat: String(latitude), lon: String(longitude) })
  const data = await request(`/data/context?${qs}`)
  return data && typeof data.context === 'object' && data.context !== null ? data.context : data
}

// Hourly forecast for the Start page's "When?" strip, straight from Open-Meteo
// (free, no key) until the backend serves a forecast. Coordinates are rounded
// to 2 dp (~1 km) before they leave the phone.
// returns: [{ time: Date, temp, rain (0-100), uv }] for the next 7 days.
export async function getHourlyForecast({ latitude, longitude }) {
  const qs = new URLSearchParams({
    latitude: latitude.toFixed(2),
    longitude: longitude.toFixed(2),
    hourly: 'temperature_2m,precipitation_probability,uv_index',
    timezone: 'Australia/Melbourne',
    forecast_days: '7'
  })
  const res = await fetch(`https://api.open-meteo.com/v1/forecast?${qs}`)
  if (!res.ok) throw new ApiError('Forecast unavailable.', res.status)
  const h = (await res.json()).hourly ?? {}
  return (h.time ?? []).map((t, i) => ({
    time: new Date(t),
    temp: h.temperature_2m?.[i] ?? null,
    rain: h.precipitation_probability?.[i] ?? null,
    uv: h.uv_index?.[i] ?? null
  }))
}

// Step illustration SVG, served by the backend from server/app/assets.
// figure is the id POST /missions puts on each step.
export function figureUrl(figure) {
  return `${BASE_URL}/assets/figures/${encodeURIComponent(figure)}.svg`
}

// GET /locations/autocomplete?q=&limit=
// returns Vicmap addresses restricted to the three pilot LGAs.
export function searchAddresses(query, { signal } = {}) {
  const qs = new URLSearchParams({ q: query, limit: '5' })
  return request(`/locations/autocomplete?${qs}`, { signal })
}

// POST /verify-step?prompt_id=&attempt= (story 6.3)
// body: the raw image (EXIF-free JPEG), not multipart, so the server can keep it
// in memory. Query: prompt_id and attempt (1-3) only. Never a run id, record
// data or any journal photo; the server rejects any other parameter.
// returns: { result: 'confirmed' | 'retry' | 'use_tap', attempts_left, checked_by }
// Any failure (offline, endpoint not live, no scorer, or no answer within
// timeoutMs) throws, and the run screen falls back to a tap confirm — never an
// endless spinner.
export async function postVerifyStep({ image, promptId, attempt, timeoutMs = 8000 }) {
  const query = new URLSearchParams({ prompt_id: String(promptId ?? ''), attempt: String(attempt) })
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  let res
  try {
    res = await fetch(`${BASE_URL}/verify-step?${query}`, {
      method: 'POST',
      body: image,
      headers: { Accept: 'application/json', 'Content-Type': 'image/jpeg' },
      signal: ctrl.signal
    })
  } catch {
    throw new ApiError('Could not reach the photo check.', 0)
  } finally {
    clearTimeout(timer)
  }
  if (!res.ok) throw new ApiError('The photo check is unavailable.', res.status)
  return res.json()
}

// POST /missions
// body: { combo_id, age_band, duration_bucket, preferences, recent_template_ids }
// age_band is "5-7" | "8-10" | "11-12" (preferencesStore.ageBand values already
// match this exactly). combo_id is the place_id from a /recommendations combo.
// returns: { missions: [...] } — a generate_missions failure degrades to
// { missions: [], degraded: true, message } rather than an HTTP error, so
// the caller checks `missions.length`, not just whether the request threw.
export function postMissions({ comboId, ageBand, durationBucket, preferences = [], recentTemplateIds = [] }) {
  return request('/missions', {
    method: 'POST',
    body: JSON.stringify({
      combo_id: comboId,
      age_band: ageBand,
      duration_bucket: durationBucket,
      preferences,
      recent_template_ids: recentTemplateIds
    })
  })
}
