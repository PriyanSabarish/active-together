import { defineStore } from 'pinia'
import { postMissions } from './api'

// ---------------------------------------------------------------------------
// F14 — mission data model. F15-F18 (preview, pick, run, overview) all read
// the same shape instead of each screen inventing its own — MOCK_MISSIONS
// below documents that shape and is kept as a fallback for when POST
// /missions degrades (backend returns { missions: [], degraded: true }) or
// fails outright, so Play/Pick never show a completely empty screen.
//
// A mission's live progress is a single number (`stepIndex`), not a status per
// step, so the run screen (F17) and the overview screen (F18) can never show
// two different ideas of how far along the mission is — both derive per-step
// status from the same getter here.
// ---------------------------------------------------------------------------

// Converts one backend Mission into the flat shape these screens render.
// verify_mode 'photo' maps to 'photo', everything else ('self') to 'tap' —
// the UI has always only known a binary confirm type. whyThisMission has no
// backend field to draw from (Mission carries no explanation, unlike Combo),
// so it's composed client-side from what's on hand.
export function mapMission(mission, { placeName, category, reason }) {
  return {
    id: mission.mission_id,
    templateId: mission.template_id,
    title: mission.title,
    placeName,
    category,
    ageBand: mission.age_band,
    durationMin: mission.estimated_minutes,
    equipment: mission.equipment?.length ? mission.equipment.join(', ') : 'None — everyday clothes and shoes only.',
    whyThisMission: reason,
    steps: mission.steps.map((s) => ({
      title: s.prompt_text,
      confirm: s.verify_mode === 'photo' ? 'photo' : 'tap'
    }))
  }
}

export const MOCK_MISSIONS = [
  {
    id: 'bark-detective',
    title: 'Bark Detective',
    placeName: 'Fawkner Park',
    category: 'playground', // CATEGORY_META key (store.js) — groups F22's activity mix
    ageBand: '8-10',
    durationMin: 20,
    equipment: 'None — everyday clothes and shoes only.',
    whyThisMission: "Matches Daniel's \"playground play\" preference and hasn't been used in the last 5 outings.",
    steps: [
      { title: 'Find a tree with smooth bark', confirm: 'tap' },
      { title: 'Find a tree with bumpy bark', confirm: 'photo' },
      { title: 'Say which bark you liked most', confirm: 'tap' }
    ]
  },
  {
    id: 'shadow-tag',
    title: 'Shadow Tag',
    placeName: 'Princes Park Reserve',
    category: 'sports_ground',
    ageBand: '8-10',
    durationMin: 15,
    equipment: 'None — works best in direct sun.',
    whyThisMission: "A quick, active pick for a sporting ground with no equipment on hand.",
    steps: [
      { title: "Chase and copy each other's shadow shapes", confirm: 'tap' },
      { title: 'Make a shadow shape Daniel has to guess', confirm: 'tap' }
    ]
  },
  {
    id: 'cloud-spotting',
    title: 'Cloud Spotting',
    placeName: 'Royal Park Trail',
    category: 'trail_access',
    ageBand: '8-10',
    durationMin: 15,
    equipment: 'None.',
    whyThisMission: 'A calm option for a windier day, along a trail with open sky.',
    steps: [
      { title: 'Find a cloud that looks like an animal', confirm: 'tap' },
      { title: 'Name the shapes you find in the clouds', confirm: 'photo' }
    ]
  }
]

export const useMissionStore = defineStore('mission', {
  state: () => ({
    candidates: [], // options offered by Pick-a-mission (F16); empty until fetchMissions runs
    loading: false,
    error: '', // set on a hard failure (network/4xx/5xx) — a degraded-but-200 response is not an error
    active: null, // the chosen Mission object, or null before one is picked
    stepIndex: 0, // index of the step currently in progress within active.steps
    status: 'not_started', // 'not_started' | 'in_progress' | 'done'
    // Set when a parent ends a mission early (AC-8.1.4): it is never written to
    // history as complete. Play shows it once, then clears it.
    lastAbandoned: null // { title, placeName, doneCount, totalSteps } | null
  }),
  getters: {
    totalSteps(state) {
      return state.active?.steps.length ?? 0
    },
    // One entry per step: 'done' | 'active' | 'todo'. F17 (run) and F18
    // (overview) both read this instead of tracking progress themselves.
    stepStates(state) {
      if (!state.active) return []
      return state.active.steps.map((_, i) => {
        if (state.status === 'done') return 'done'
        if (i < state.stepIndex) return 'done'
        if (i === state.stepIndex && state.status === 'in_progress') return 'active'
        return 'todo'
      })
    },
    currentStep(state) {
      return state.active?.steps[state.stepIndex] ?? null
    }
  },
  actions: {
    // Calls POST /missions for one chosen place and fills `candidates` from
    // the response, mapped into the shape every mission screen expects.
    // `place` is a mapped search-result place (store.js mapCombo output) —
    // place.id is the combo_id (== the backend's place_id, see
    // app.recommendation.recommend), place.durationBucket is the plan
    // already agreed on Detail. reason is composed here since Mission
    // carries no explanation field of its own (unlike Combo).
    //
    // A degraded-but-200 response ({ missions: [], degraded: true }) clears
    // `error` and leaves `candidates` empty rather than throwing — Pick/Play
    // show their own "nothing chosen yet" states for that, same as a
    // genuinely empty result. A network/4xx/5xx failure sets `error` instead.
    async fetchMissions(place, { ageBand, preferences = [], recentTemplateIds = [] }) {
      this.loading = true
      this.error = ''
      try {
        const data = await postMissions({
          comboId: place.id,
          ageBand,
          durationBucket: place.durationBucket,
          preferences,
          recentTemplateIds
        })
        const reason = `Matches ${place.name} and your current preferences.`
        this.candidates = (data.missions ?? []).map((m) =>
          mapMission(m, { placeName: place.name, category: place.category, reason })
        )
      } catch (e) {
        this.candidates = []
        this.error = e?.message ?? 'Something went wrong.'
      } finally {
        this.loading = false
      }
    },
    chooseMission(missionId) {
      const mission = this.candidates.find((m) => m.id === missionId)
      if (!mission) return
      this.active = mission
      this.stepIndex = 0
      this.status = 'not_started'
    },
    startMission() {
      if (!this.active) return
      this.status = 'in_progress'
      this.stepIndex = 0
    },
    // Skip is deliberately the same transition as confirm — the walkthrough
    // treats them as equally weighted, "nothing is a fail".
    advanceStep() {
      if (!this.active || this.status !== 'in_progress') return
      if (this.stepIndex < this.active.steps.length - 1) {
        this.stepIndex += 1
      } else {
        this.status = 'done'
      }
    },
    // Gap 5 — end a running mission without logging it as complete. Steps
    // already done are kept on the notice so the parent sees they counted.
    abandonMission() {
      if (!this.active || this.status !== 'in_progress') return
      this.lastAbandoned = {
        title: this.active.title,
        placeName: this.active.placeName,
        doneCount: this.stepIndex,
        totalSteps: this.active.steps.length
      }
      this.resetMission()
    },
    clearAbandoned() {
      this.lastAbandoned = null
    },
    resetMission() {
      this.active = null
      this.stepIndex = 0
      this.status = 'not_started'
    }
  }
})
