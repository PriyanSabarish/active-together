import { describe, expect, it } from 'vitest'
import { sanitise } from '../../client/src/persist'

describe('search state persistence', () => {
  it('keeps a bounded selected address', () => {
    const saved = sanitise({
      selectedAddress: {
        id: 42,
        label: '1 Centre Road Clayton VIC 3168',
        latitude: -37.927,
        longitude: 145.12,
        suburb: 'Clayton',
        postcode: '3168'
      }
    })

    expect(saved.selectedAddress).toEqual({
      id: '42',
      label: '1 Centre Road Clayton VIC 3168',
      latitude: -37.927,
      longitude: 145.12,
      suburb: 'Clayton',
      postcode: '3168'
    })
  })

  it('drops an address without finite coordinates', () => {
    const saved = sanitise({
      selectedAddress: { label: 'Tampered', latitude: 'not-a-number', longitude: 145.12 }
    })

    expect(saved).not.toHaveProperty('selectedAddress')
  })
})