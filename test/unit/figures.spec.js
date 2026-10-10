// Iteration 3 — stick-figure step illustrations: the figure id survives
// mapping from POST /missions, and fetched SVG is sanitised before inlining.

import { describe, it, expect } from 'vitest'
import { sanitizeSvg } from '../../client/src/figures'
import { mapMission } from '../../client/src/missionStore'
import { figureUrl } from '../../client/src/api'

describe('stick figures', () => {
  it('mapMission keeps each step\'s figure id (null when absent)', () => {
    const m = mapMission({
      mission_id: 'm1', template_id: 't1', title: 'Follow the leader', age_band: '8-10', estimated_minutes: 20,
      steps: [
        { sequence: 1, prompt_text: 'Copy how I walk.', verify_mode: 'self', figure: 'follow_me_walk' },
        { sequence: 2, prompt_text: 'Find a leaf.', verify_mode: 'photo', prompt_id: 'p_leaf' }
      ]
    }, { placeName: 'Park', category: 'playground', reason: '' })
    expect(m.steps.map((s) => s.figure)).toEqual(['follow_me_walk', null])
  })

  it('figure URLs point at the backend static mount', () => {
    expect(figureUrl('leaf_simple')).toMatch(/\/assets\/figures\/leaf_simple\.svg$/)
  })

  it('sanitizeSvg strips scripts, handlers and outside links but keeps drawing and embedded images', () => {
    const out = sanitizeSvg(`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 280 132" onload="alert(1)">
      <script>alert(2)</script>
      <path d="M1 1L9 9" stroke="currentColor" onclick="alert(3)"/>
      <image href="data:image/png;base64,AAAA"/>
      <a href="https://evil.example"><circle r="2"/></a>
    </svg>`)
    expect(out).not.toMatch(/script|onload|onclick|evil\.example/)
    expect(out).toMatch(/stroke="currentColor"/)
    expect(out).toMatch(/data:image\/png;base64,AAAA/)
    expect(out).toMatch(/width="100%"/)
  })

  it('sanitizeSvg rejects anything that is not an SVG', () => {
    expect(sanitizeSvg('<html><body>404</body></html>')).toBe('')
    expect(sanitizeSvg('{"detail":"Not Found"}')).toBe('')
  })
})
