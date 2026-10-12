// F66 / F67 — storage quota notice and the iPhone add-to-home-screen prompt.

import { describe, it, expect } from 'vitest'
import { isNearQuota, needsHomeScreenPrompt } from '../../client/src/storageNotice'
import { bestStreak } from '../../client/src/historyStore'

describe('storage notice (about 80% of quota)', () => {
  it('is off below 80% and on at or above it', () => {
    expect(isNearQuota({ usage: 79, quota: 100 })).toBe(false)
    expect(isNearQuota({ usage: 80, quota: 100 })).toBe(true)
    expect(isNearQuota({ usage: 95, quota: 100 })).toBe(true)
  })
  it('stays quiet when the browser gives no estimate', () => {
    expect(isNearQuota(undefined)).toBe(false)
    expect(isNearQuota({ usage: 5 })).toBe(false)
    expect(isNearQuota({ usage: 5, quota: 0 })).toBe(false)
  })
})

describe('add to Home Screen prompt', () => {
  const iphone = { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)' }
  it('shows on iPhone in the browser, not once installed', () => {
    expect(needsHomeScreenPrompt(iphone, false)).toBe(true)
    expect(needsHomeScreenPrompt(iphone, true)).toBe(false)
  })
  it('does not show on Android or desktop', () => {
    expect(needsHomeScreenPrompt({ userAgent: 'Mozilla/5.0 (Linux; Android 14)' }, false)).toBe(false)
    expect(needsHomeScreenPrompt({ userAgent: 'Mozilla/5.0 (Windows NT 10.0)' }, false)).toBe(false)
  })
})

describe('personal best streak (D5)', () => {
  const rec = (date) => ({ date })
  it('is the longest run of consecutive weeks, and a break does not lower it', () => {
    // weeks of 2026-09-07, 09-14, 09-21 then a gap, then 10-05
    const records = [rec('2026-09-08'), rec('2026-09-15'), rec('2026-09-22'), rec('2026-10-06')]
    expect(bestStreak(records)).toBe(3)
  })
  it('counts several outings in one week once, and is 0 with none', () => {
    expect(bestStreak([rec('2026-09-08'), rec('2026-09-09'), rec('2026-09-10')])).toBe(1)
    expect(bestStreak([])).toBe(0)
  })
})
