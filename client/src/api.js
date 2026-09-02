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
  } catch {
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
// body: { latitude, longitude, radius_km, duration_min }
// returns: { status: 'ok' | 'zero_results' | 'out_of_bounds', combos: [...], message? }
export function postRecommendations({ latitude, longitude, radiusKm, durationMin }) {
  return request('/recommendations', {
    method: 'POST',
    body: JSON.stringify({
      latitude,
      longitude,
      radius_km: radiusKm,
      duration_min: durationMin
    })
  })
}

// GET /data/context?lat=&lon=
// returns the current Open-Meteo readings for a point:
// { available, temp_c, precip_prob, wind_gust_kmh, uv_index, pm25, pm10 }
export function getContext({ latitude, longitude }) {
  const qs = new URLSearchParams({ lat: String(latitude), lon: String(longitude) })
  return request(`/data/context?${qs}`)
}
