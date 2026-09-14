import { defineStore } from 'pinia'

// ---------------------------------------------------------------------------
// F14 — mission data model, on mock data only. No UI reads this yet; it exists
// so F15-F18 (preview, pick, run, overview) all read the same shape instead of
// each screen inventing its own. Swap MOCK_MISSIONS for a real POST /missions
// call once Backend A's endpoint is stable — the shape below is the contract
// those screens are written against.
//
// A mission's live progress is a single number (`stepIndex`), not a status per
// step, so the run screen (F17) and the overview screen (F18) can never show
// two different ideas of how far along the mission is — both derive per-step
// status from the same getter here.
// ---------------------------------------------------------------------------

export const MOCK_MISSIONS = [
  {
    id: 'bark-detective',
    title: 'Bark Detective',
    placeName: 'Fawkner Park',
    category: 'playground', // CATEGORY_META key (store.js) — groups F22's activity mix
    ageBand: '6-8',
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
    ageBand: '6-8',
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
    ageBand: '6-8',
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
    candidates: MOCK_MISSIONS, // options offered by Pick-a-mission (F16)
    active: null, // the chosen Mission object, or null before one is picked
    stepIndex: 0, // index of the step currently in progress within active.steps
    status: 'not_started' // 'not_started' | 'in_progress' | 'done'
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
    resetMission() {
      this.active = null
      this.stepIndex = 0
      this.status = 'not_started'
    }
  }
})
