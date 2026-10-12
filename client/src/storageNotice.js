// Storage and install notices for photos kept on the phone (stories 10.4, F66, F67).
// Nothing is deleted automatically (D14): the parent is only told.

export const QUOTA_NOTICE_RATIO = 0.8

// True once the app uses about 80% of the browser's storage quota.
export function isNearQuota(estimate, ratio = QUOTA_NOTICE_RATIO) {
  const usage = Number(estimate?.usage)
  const quota = Number(estimate?.quota)
  if (!Number.isFinite(usage) || !Number.isFinite(quota) || quota <= 0) return false
  return usage / quota >= ratio
}

export async function storageIsNearlyFull() {
  try {
    const estimate = await navigator.storage?.estimate?.()
    return isNearQuota(estimate)
  } catch {
    return false
  }
}

// iPhone Safari clears site data after a stretch of non-use unless the app is
// added to the Home Screen, so photos are only safe there once it is installed.
export function needsHomeScreenPrompt(nav = globalThis.navigator, standalone = isStandalone()) {
  const ua = nav?.userAgent ?? ''
  const iOS = /iPhone|iPad|iPod/.test(ua) || (nav?.platform === 'MacIntel' && nav?.maxTouchPoints > 1)
  return iOS && !standalone
}

export function isStandalone() {
  try {
    return globalThis.matchMedia?.('(display-mode: standalone)').matches === true || globalThis.navigator?.standalone === true
  } catch {
    return false
  }
}
