// Small line icons for mission tasks (24x24 paths, stroke only). Keys match
// `icon` on a mission step; anything unknown falls back to the sun.
export const TASK_ICON = {
  sun: 'M12 4v2 M12 18v2 M4 12h2 M18 12h2 M6.3 6.3l1.4 1.4 M16.3 16.3l1.4 1.4 M17.7 6.3l-1.4 1.4 M7.7 16.3l-1.4 1.4 M12 8.2a3.8 3.8 0 1 0 0 7.6 3.8 3.8 0 0 0 0-7.6',
  ruler: 'M4 9h16v6H4z M8 9v3 M12 9v3 M16 9v3',
  paw: 'M12 13.5c2.6 0 4.5 1.6 4.5 3.4S14.6 20 12 20s-4.5-1.3-4.5-3.1 1.9-3.4 4.5-3.4 M7 9.5a1.6 1.6 0 1 0 0-3.2 1.6 1.6 0 0 0 0 3.2 M17 9.5a1.6 1.6 0 1 0 0-3.2 1.6 1.6 0 0 0 0 3.2 M10 7.4a1.6 1.6 0 1 0 0-3.2 1.6 1.6 0 0 0 0 3.2 M14 7.4a1.6 1.6 0 1 0 0-3.2 1.6 1.6 0 0 0 0 3.2',
  wind: 'M3 8h11a2.6 2.6 0 1 0-2-4.3 M3 16h8a2.4 2.4 0 1 1-1.8 4 M3 12h17',
  moon: 'M19 14.5A8 8 0 0 1 9.5 5a8 8 0 1 0 9.5 9.5',
  eye: 'M2.5 12S6 5.8 12 5.8 21.5 12 21.5 12 18 18.2 12 18.2 2.5 12 2.5 12 M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6',
  drop: 'M12 3.5s6 6.6 6 10.4a6 6 0 0 1-12 0C6 10.1 12 3.5 12 3.5z',
  leaf: 'M4.5 19.5C4.5 11 11 4.5 19.5 4.5c0 8.5-6.5 15-15 15z M9 15l6-6',
  hand: 'M8 11V5.6a1.6 1.6 0 1 1 3.2 0V11 M11.2 10.6V4.9a1.6 1.6 0 1 1 3.2 0V11 M14.4 11V6.6a1.6 1.6 0 1 1 3.2 0V14a6 6 0 0 1-6 6h-1a5.6 5.6 0 0 1-5.6-5.6v-3a1.6 1.6 0 1 1 3.2 0',
  rock: 'M5 17l3.5-9 5 3.5 3-2.5 2.5 8z',
  spiral: 'M12 12a2.5 2.5 0 1 1 2.5 2.5A4.5 4.5 0 0 1 10 10a6.5 6.5 0 0 1 6.5 6.5',
  flower: 'M12 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5 M12 9.5V4.5 M12 14.5v5 M9.5 12h-5 M14.5 12h5'
}

export function taskIcon(key) {
  return TASK_ICON[key] ?? TASK_ICON.sun
}

// Journal glyphs from the Canvas design (Week diary, outing detail, You).
export const TREE = 'M12 2 L15.2 7 L13.3 7 L17.2 12 L15.1 12 L19.2 17 L13 17 L13 20.3 L11 20.3 L11 17 L4.8 17 L8.9 12 L6.8 12 L10.7 7 L8.8 7 Z'
export const OVAL = 'M4 20v-8a8 8 0 0 1 16 0v8 M2.5 20h19 M8 20v-5 M16 20v-5'
export const STAR = 'M12 3l2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4z'
export const HOUSE = 'M4 11.5 12 5l8 6.5 M6 10v9.5h12V10 M10 19.5v-5h4v5'
export const CAMERA = 'M4 8.5h3l1.6-2.5h6.8L17 8.5h3v11H4z M12 10.1a3.4 3.4 0 1 0 0 6.8 3.4 3.4 0 0 0 0-6.8'
export const PIN = 'M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z M12 12.3a2.3 2.3 0 1 0 0-4.6 2.3 2.3 0 0 0 0 4.6'
export const SHAPES = 'M7 3.5l4 7H3z M17 14a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7 M13.5 4h7v7h-7z M3.5 14h7v7h-7z'
export const CALENDAR = 'M4 6.5h16v13.5H4V6.5Z M4 10.5h16 M8.5 3.5v4 M15.5 3.5v4'
export const THUMB_UP = 'M7 20.5V10 M7 11.5l4.2-8a2 2 0 0 1 3.6 1.6L14 10h3.8a2.4 2.4 0 0 1 2.3 3l-1.5 6a2.4 2.4 0 0 1-2.3 1.5H7'
export const THUMB_DOWN = 'M7 3.5V14 M7 12.5l4.2 8a2 2 0 0 0 3.6-1.6L14 14h3.8a2.4 2.4 0 0 0 2.3-3l-1.5-6A2.4 2.4 0 0 0 16.3 3.5H7'

// Place icon per backend category (CATEGORY_META in store.js).
export const CATEGORY_ICON = {
  playground: TREE,
  park_and_garden: TASK_ICON.leaf,
  picnic_day_use: TASK_ICON.flower,
  sports_ground: OVAL,
  court: SHAPES,
  skate_bmx: TASK_ICON.wind,
  trail_access: STAR,
  home: HOUSE
}

export function categoryIcon(key) {
  return CATEGORY_ICON[key] ?? TREE
}

const FACE = 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M9 10v.01 M15 10v.01 '
// Child's feedback faces, keyed by FEEDBACK_OPTIONS ids (historyStore.js).
export const FEEDBACK_ICON = {
  fun: FACE + 'M8.5 14.2a4 4 0 0 0 7 0',
  boring: FACE + 'M8.5 15.2h7',
  too_hard: FACE + 'M7.8 15.6q1.05-1.3 2.1 0t2.1 0 2.1 0 2.1 0',
  too_easy: FACE + 'M13.6 7.2q1.6-1.4 3.2-.6 M9 15q3 1.4 6-.6'
}
