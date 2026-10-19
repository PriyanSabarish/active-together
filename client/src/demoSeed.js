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

// Shows or hides the demo outings to match the switch. Real outings are kept
// either way: with the demo on, new outings sit on top of the sample ones.
export function seedDemoData() {
  const history = useHistoryStore()
  const prefs = usePreferencesStore()

  if (!demoEnabled()) {
    history.setDemoRecords([])
    return
  }

  {
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
      // Four active days in the last week (one outing each), the rest inactive, relative to today so they stay
      // recent whatever day the app is opened.
      rec(iso(new Date(), -6), '11:00 am', 'Napier Park', 'playground', 'Playground', 25, 'too_easy', '#D9CDB4', 1, 3),
      rec(iso(new Date(), -4), '4:05 pm', 'Central Reserve', 'trail_access', 'Exploring', 40, 'fun', '#E6D8BE', 2, 3),
      rec(iso(new Date(), -2), '10:15 am', 'Jells Park', 'trail_access', 'Trail walk', 55, 'fun', '#BFD4B0', 2, 3),
      rec(iso(new Date(), -1), '9:30 am', 'Fawkner Park', 'playground', 'Shadow Detective', 30, 'fun', '#C9DBBE', 2, 3)
    ]
      // One outing a day: older samples that land on one of those days make way.
      .filter((r, i, all) => r.date <= localIso() && (i >= all.length - 4 || !all.slice(-4).some((x) => x.date === r.date)))
    history.setDemoRecords(seed)
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
