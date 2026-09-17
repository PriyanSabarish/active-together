import { mondayOf, useHistoryStore } from './historyStore'
import { usePreferencesStore } from './preferencesStore'

// ---------------------------------------------------------------------------
// Demo data for Insights and Prefs. Both screens are device-local only and
// will not talk to the backend; the real, editable versions land in the final
// iteration. Until then the app boots with a believable week so the screens
// aren't empty. Records are dated relative to the current week so the mock
// never goes stale. Store defaults stay empty (the unit tests rely on that).
// ---------------------------------------------------------------------------

function iso(base, offsetDays) {
  const d = new Date(base)
  d.setDate(base.getDate() + offsetDays)
  return d.toISOString().slice(0, 10)
}

const rec = (date, time, placeName, category, missionTitle, durationMin, feedback, photoStepsCount = 1, totalSteps = 3) => ({
  date, time, placeName, category, missionTitle, durationMin, feedback, photoStepsCount, totalSteps
})

export const DEMO_KEY = 'at-demo-data'

export function demoEnabled() {
  try {
    return localStorage.getItem(DEMO_KEY) !== 'off'
  } catch {
    return true
  }
}

export function setDemoEnabled(on) {
  try {
    localStorage.setItem(DEMO_KEY, on ? 'on' : 'off')
  } catch {
    /* storage unavailable */
  }
}

export function seedDemoData() {
  if (!demoEnabled()) return
  const history = useHistoryStore()
  const prefs = usePreferencesStore()

  if (history.records.length === 0) {
    const thisMon = mondayOf(new Date())
    const lastMon = new Date(thisMon)
    lastMon.setDate(thisMon.getDate() - 7)

    // Oldest first, so the newest ends up at the top of the list.
    const seed = [
      rec(iso(lastMon, 1), '4:10 pm', 'Napier Park', 'playground', 'Colour Hunt', 25, 'fun'),
      rec(iso(lastMon, 4), '10:30 am', 'Jells Park', 'trail_access', 'Cloud Spotting', 55, null, 1, 2),
      rec(iso(thisMon, 1), '4:05 pm', 'Central Reserve', 'sports_ground', 'Shadow Tag', 40, 'fun', 0, 2),
      rec(iso(thisMon, 3), '3:50 pm', 'Napier Park', 'playground', 'Bark Detective', 25, 'too_easy'),
      rec(iso(thisMon, 5), '10:15 am', 'Jells Park', 'trail_access', 'Texture Trail', 55, 'fun', 2, 3)
    ]
    seed.forEach((r) => history.addRecord(r))
  }

  // A spread of likes / neutral / not-for-me so the Prefs cards show all three tags.
  prefs.setAffinity('playground', 80)
  prefs.setAffinity('trail_access', 80)
  prefs.setAffinity('park_and_garden', 50)
  prefs.setAffinity('picnic_day_use', 50)
  prefs.setAffinity('court', 50)
  prefs.setAffinity('skate_bmx', 50)
  prefs.setAffinity('sports_ground', 20)
}
