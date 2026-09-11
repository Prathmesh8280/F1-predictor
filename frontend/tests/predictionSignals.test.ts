import { describe, it, expect } from 'vitest'
import {
  movers,
  driverReasons,
  signalSummary,
  predictionSentence,
} from '../src/lib/predictionSignals'
import type { PredictionRow } from '../src/types'

function row(partial: Partial<PredictionRow>): PredictionRow {
  return {
    rank: 1, driver: 'VER', team: 'Red Bull', grid_pos: 1, actual_rank: null,
    championship_rank: null, constructor_rank: null, fp2_pace_rank: null,
    delta1: null, stage2_used: false, ...partial,
  }
}

describe('movers — position delta calculation', () => {
  const rows = [
    row({ driver: 'A', grid_pos: 5, rank: 1 }),   // +4 gainer
    row({ driver: 'B', grid_pos: 2, rank: 4 }),   // -2 loser
    row({ driver: 'C', grid_pos: 3, rank: 3 }),   // 0, excluded
    row({ driver: 'D', grid_pos: 10, rank: 2 }),  // +8 gainer
  ]

  it('separates gainers and losers by grid_pos - rank', () => {
    const { gainers, losers } = movers(rows)
    expect(gainers.map(m => m.row.driver)).toEqual(['D', 'A']) // sorted by biggest gain
    expect(gainers.map(m => m.delta)).toEqual([8, 4])
    expect(losers.map(m => m.row.driver)).toEqual(['B'])
    expect(losers[0].delta).toBe(-2)
  })

  it('excludes drivers with zero delta', () => {
    const { gainers, losers } = movers(rows)
    const all = [...gainers, ...losers].map(m => m.row.driver)
    expect(all).not.toContain('C')
  })

  it('respects the count limit', () => {
    const { gainers } = movers(rows, 1)
    expect(gainers).toHaveLength(1)
    expect(gainers[0].row.driver).toBe('D')
  })
})

describe('driverReasons — only aligned with predicted direction', () => {
  it('returns positive reasons for a gaining driver', () => {
    const r = row({ grid_pos: 8, rank: 2, stage2_used: true, fp2_pace_rank: 3, championship_rank: 4 })
    const reasons = driverReasons(r)
    expect(reasons.every(x => x.kind === 'pos')).toBe(true)
    expect(reasons.map(x => x.label)).toContain('Strong weekend pace')
    expect(reasons.map(x => x.label)).toContain('Strong championship form')
  })

  it('returns negative reasons for a losing driver', () => {
    const r = row({ grid_pos: 2, rank: 8, stage2_used: true, fp2_pace_rank: 10, championship_rank: 12 })
    const reasons = driverReasons(r)
    expect(reasons.every(x => x.kind === 'neg')).toBe(true)
  })

  it('returns no signal reasons when stage2 not used', () => {
    const r = row({ grid_pos: 5, rank: 1, stage2_used: false, fp2_pace_rank: 1 })
    expect(driverReasons(r)).toEqual([])
  })
})

describe('signalSummary', () => {
  it('always includes qualifying, adds stage2 lines when used', () => {
    const r = row({ grid_pos: 3, stage2_used: true, fp2_pace_rank: 1, championship_rank: 4, constructor_rank: 3 })
    const lines = signalSummary(r)
    expect(lines[0]).toEqual({ label: 'Qualifying', value: 'P3' })
    const labels = lines.map(l => l.label)
    expect(labels).toEqual(['Qualifying', 'Weekend pace', 'Championship', 'Constructor'])
  })

  it('omits stage2 lines when stage2 not used', () => {
    const r = row({ grid_pos: 3, stage2_used: false })
    expect(signalSummary(r)).toHaveLength(1)
  })
})

describe('predictionSentence', () => {
  it('describes gains, losses, and holds with correct pluralization', () => {
    expect(predictionSentence(row({ driver: 'X', grid_pos: 5, rank: 4 }))).toContain('gain 1 position')
    expect(predictionSentence(row({ driver: 'X', grid_pos: 2, rank: 5 }))).toContain('lose 3 positions')
    expect(predictionSentence(row({ driver: 'X', grid_pos: 4, rank: 4 }))).toContain('hold P4')
  })
})
