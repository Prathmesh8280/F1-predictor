import { describe, it, expect } from 'vitest'
import { CIRCUIT_META, ROUND_MAP_2026, circuitByRound, RACE_NAMES } from '../src/constants/races'

describe('ROUND_MAP_2026 / circuitByRound', () => {
  it('maps the two Spanish races to distinct circuits', () => {
    // R7 = Barcelona GP → Spain; R14 = Spanish GP → Madrid Ring.
    expect(circuitByRound(7)).toBe('Spain')
    expect(circuitByRound(14)).toBe('Madrid')
  })

  it('maps early rounds correctly', () => {
    expect(circuitByRound(1)).toBe('Australia')
    expect(circuitByRound(6)).toBe('Monaco')
    expect(circuitByRound(13)).toBe('Italy')
  })

  it('returns undefined for an unmapped round', () => {
    expect(circuitByRound(99)).toBeUndefined()
  })

  it('is the inverse of each circuit round2026 field', () => {
    for (const [key, meta] of Object.entries(CIRCUIT_META)) {
      if (meta.round2026 != null) {
        expect(ROUND_MAP_2026[meta.round2026]).toBe(key)
      }
    }
  })
})

describe('CIRCUIT_META integrity', () => {
  it('includes both Spain and Madrid as separate entries', () => {
    expect(RACE_NAMES).toContain('Spain')
    expect(RACE_NAMES).toContain('Madrid')
    expect(CIRCUIT_META['Madrid'].officialName).toBe('Spanish Grand Prix')
    expect(CIRCUIT_META['Spain'].officialName).toBe('Barcelona Grand Prix')
  })

  it('every circuit has a valid overtaking rating and a track image URL', () => {
    const valid = ['VERY HIGH', 'HIGH', 'MEDIUM', 'LOW', 'VERY LOW']
    for (const meta of Object.values(CIRCUIT_META)) {
      expect(valid).toContain(meta.overtaking)
      expect(meta.trackImgUrl).toMatch(/^https?:\/\//)
    }
  })
})
