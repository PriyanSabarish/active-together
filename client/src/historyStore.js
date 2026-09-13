import { defineStore } from 'pinia'

// ---------------------------------------------------------------------------
// F20 — completed-mission history, written to by MissionFinishedView (F19)
// and read by Today's this-week count (F21) and Weekly insights (F22/F23).
//
// In-memory only for now. Whether this needs to survive a reload (localStorage
// / IndexedDB) or become a server record is an open item in the doc
// ("Insights persistence") with no owner yet — not decided here.
// ---------------------------------------------------------------------------

function mondayOf(date) {
  const d = new Date(date)
  const day = d.getDay() // 0 = Sunday
  const diff = (day === 0 ? -6 : 1) - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function inWeek(date, weekStart) {
  const weekEnd = new Date(weekStart)
  weekEnd.setDate(weekStart.getDate() + 7)
  return date >= weekStart && date < weekEnd
}

// Four equal, unranked options (F19) — never shown as a score.
export const FEEDBACK_OPTIONS = [
  { id: 'fun', label: 'Fun', emoji: '🙂' },
  { id: 'boring', label: 'Boring', emoji: '😐' },
  { id: 'too_hard', label: 'Too hard', emoji: '😣' },
  { id: 'too_easy', label: 'Too easy', emoji: '😴' }
]

export function feedbackEmoji(id) {
  return FEEDBACK_OPTIONS.find((f) => f.id === id)?.emoji ?? ''
}

export function feedbackLabel(id) {
  return FEEDBACK_OPTIONS.find((f) => f.id === id)?.label ?? ''
}

export function relativeDayLabel(dateStr) {
  const d = new Date(dateStr)
  const startOfDay = (x) => { const c = new Date(x); c.setHours(0, 0, 0, 0); return c }
  const days = Math.round((startOfDay(new Date()) - startOfDay(d)) / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  return d.toLocaleDateString(undefined, { weekday: 'long' })
}

export const useHistoryStore = defineStore('history', {
  state: () => ({
    records: [] // newest first: { id, date, time, placeName, category, missionTitle, durationMin, photoStepsCount, totalSteps, feedback }
  }),
  getters: {
    thisWeekCount(state) {
      const weekStart = mondayOf(new Date())
      return state.records.filter((r) => inWeek(new Date(r.date), weekStart)).length
    },
    lastWeekCount(state) {
      const lastWeekStart = mondayOf(new Date())
      lastWeekStart.setDate(lastWeekStart.getDate() - 7)
      return state.records.filter((r) => inWeek(new Date(r.date), lastWeekStart)).length
    },
    mostRecent(state) {
      return state.records[0] ?? null
    },
    byDate(state) {
      const map = {}
      for (const r of state.records) {
        map[r.date] = map[r.date] ?? []
        map[r.date].push(r)
      }
      return map
    }
  },
  actions: {
    addRecord(record) {
      this.records.unshift({ id: `rec-${Date.now()}`, ...record })
    }
  }
})
