import { figureUrl } from './api'

// ---------------------------------------------------------------------------
// Stick-figure illustrations for mission steps. The backend names one per
// step (step.figure in POST /missions) and serves the SVG at
// /assets/figures/<figure>.svg. The SVG is fetched and inlined rather than
// shown with <img>, so line drawings that use stroke="currentColor" take the
// run screen's colour instead of rendering black on the dark background.
//
// Inlined markup is sanitised first: scripts, foreign content, event-handler
// attributes and non-image links are removed. Any failure (offline, 404, not
// an SVG) resolves to '' and the run screen keeps its plain step icon.
// ---------------------------------------------------------------------------

const cache = new Map() // figure id -> Promise<string>

const BLOCKED = ['script', 'foreignObject', 'iframe', 'object', 'embed', 'audio', 'video']

export function sanitizeSvg(text) {
  if (typeof DOMParser === 'undefined' || typeof text !== 'string') return ''
  const doc = new DOMParser().parseFromString(text, 'image/svg+xml')
  const svg = doc.documentElement
  if (!svg || svg.nodeName.toLowerCase() !== 'svg' || doc.getElementsByTagName('parsererror').length) return ''

  for (const tag of BLOCKED) {
    for (const el of Array.from(svg.getElementsByTagName(tag))) el.remove()
  }
  for (const el of [svg, ...Array.from(svg.getElementsByTagName('*'))]) {
    for (const attr of Array.from(el.attributes)) {
      const name = attr.name.toLowerCase()
      const value = attr.value.trim().toLowerCase()
      if (name.startsWith('on')) el.removeAttribute(attr.name)
      else if ((name === 'href' || name === 'xlink:href') && !value.startsWith('#') && !value.startsWith('data:image/')) {
        el.removeAttribute(attr.name)
      }
    }
  }
  // Fill the sketch box whatever size the artwork was drawn at.
  svg.setAttribute('width', '100%')
  svg.setAttribute('height', '100%')
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet')
  svg.setAttribute('aria-hidden', 'true')
  svg.setAttribute('focusable', 'false')
  return new XMLSerializer().serializeToString(svg)
}

async function fetchFigure(id) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 6000)
  try {
    const res = await fetch(figureUrl(id), { signal: ctrl.signal })
    if (!res.ok) return ''
    return sanitizeSvg(await res.text())
  } catch {
    return ''
  } finally {
    clearTimeout(timer)
  }
}

// Inline SVG markup for a figure id, or '' when there is none to show.
export function loadFigure(id) {
  if (!id) return Promise.resolve('')
  if (!cache.has(id)) {
    const p = fetchFigure(id)
    cache.set(id, p)
    // A failed fetch is not remembered, so the next step or mission retries.
    p.then((svg) => { if (!svg) cache.delete(id) })
  }
  return cache.get(id)
}
