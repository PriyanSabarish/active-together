import { localIso, mondayOf, useHistoryStore } from './historyStore'
import { usePreferencesStore } from './preferencesStore'
import { hasSavedPreferences } from './persist'

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
  return localIso(d)
}

// tone: a colour placeholder standing in for an outing photo (demo only).
// demo: true keeps these in memory only — they are never saved to the device.
const rec = (date, time, placeName, category, missionTitle, durationMin, feedback, tone = null, photoStepsCount = 1, totalSteps = 3) => ({
  date, time, placeName, category, missionTitle, durationMin, feedback, tone, photoStepsCount, totalSteps, demo: true
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
    const weeksAgo = (n) => {
      const d = new Date(thisMon)
      d.setDate(thisMon.getDate() - 7 * n)
      return d
    }

    // Oldest first, so the newest ends up at the top of the list. Days past
    // today are skipped below, so early in the week the sample stays honest.
    const seed = [
      rec(iso(weeksAgo(3), 5), '10:20 am', 'Fawkner Park', 'playground', 'Shadow Detective', 40, 'fun', '#C9DBBE'),
      rec(iso(weeksAgo(2), 2), '4:00 pm', 'Napier Park', 'playground', 'Animal Tracker', 40, 'too_hard', '#D9CDB4'),
      rec(iso(weeksAgo(2), 6), '11:00 am', 'Jells Park', 'trail_access', 'Wind Watchers', 30, 'fun', '#C6D9DC'),
      rec(iso(weeksAgo(1), 1), '4:10 pm', 'Napier Park', 'playground', 'Colour Hunt', 25, 'fun'),
      rec(iso(weeksAgo(1), 5), '10:30 am', 'Central Reserve', 'sports_ground', 'Texture Trail', 40, null, '#D6E2C4'),
      rec(iso(thisMon, 0), '4:05 pm', 'Central Reserve', 'trail_access', 'Exploring', 40, 'fun', '#E6D8BE', 0, 2),
      rec(iso(thisMon, 1), '3:50 pm', 'Napier Park', 'playground', 'Playground', 15, 'too_easy'),
      rec(iso(thisMon, 1), '5:30 pm', 'Home', 'home', 'Obstacle course', 15, 'fun', null, 0, 3),
      rec(iso(thisMon, 3), '10:15 am', 'Jells Park', 'trail_access', 'Trail walk', 55, 'fun', '#BFD4B0', 2, 3)
    ].filter((r) => r.date <= localIso())
    seed.forEach((r) => history.addRecord(r))
  }

  // A couple of likes so the You page has something to show — only on a
  // device that has never saved its own preferences. Nothing is set to "Not
  // for me": that really removes places from the search now.
  if (hasSavedPreferences()) return
  prefs.setAffinity('playground', 80)
  prefs.setAffinity('trail_access', 80)
  prefs.setAffinity('park_and_garden', 50)
  prefs.setAffinity('picnic_day_use', 50)
  prefs.setAffinity('court', 50)
  prefs.setAffinity('skate_bmx', 50)
}
