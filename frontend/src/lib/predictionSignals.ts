import type { PredictionRow } from '../types'

// All helpers here derive strictly from real model outputs on PredictionRow.
// Nothing is invented — a reason only appears when the underlying signal
// actually supports the predicted direction (spec §6, §32).

export interface Mover {
  row: PredictionRow
  delta: number // grid_pos - rank; positive = gained places, negative = lost
}

export function movers(rows: PredictionRow[], count = 4): { gainers: Mover[]; losers: Mover[] } {
  const withDelta = rows
    .map(r => ({ row: r, delta: r.grid_pos - r.rank }))
    .filter(m => m.delta !== 0)
  const gainers = withDelta.filter(m => m.delta > 0).sort((a, b) => b.delta - a.delta).slice(0, count)
  const losers = withDelta.filter(m => m.delta < 0).sort((a, b) => a.delta - b.delta).slice(0, count)
  return { gainers, losers }
}

export interface Reason {
  label: string
  kind: 'pos' | 'neg'
}

/**
 * Human-readable reasons behind a driver's predicted movement, derived from
 * the model's own signals. A signal counts as "supporting" an upward move when
 * the driver ranks better in it than they qualified (and vice-versa). Only
 * reasons aligned with the actual predicted direction are returned, so the UI
 * never contradicts itself. Empty array = no clear signal-level explanation.
 */
export function driverReasons(r: PredictionRow): Reason[] {
  const reasons: Reason[] = []

  // Stage 2 — form + pace signals (only meaningful once standings exist).
  if (r.stage2_used) {
    if (r.fp2_pace_rank != null) {
      if (r.fp2_pace_rank < r.grid_pos) reasons.push({ label: 'Strong weekend pace', kind: 'pos' })
      else if (r.fp2_pace_rank > r.grid_pos) reasons.push({ label: 'Modest weekend pace', kind: 'neg' })
    }
    if (r.championship_rank != null) {
      if (r.championship_rank < r.grid_pos) reasons.push({ label: 'Strong championship form', kind: 'pos' })
      else if (r.championship_rank > r.grid_pos) reasons.push({ label: 'Weaker championship form', kind: 'neg' })
    }
    if (r.constructor_rank != null) {
      if (r.constructor_rank < r.grid_pos) reasons.push({ label: 'Strong constructor form', kind: 'pos' })
      else if (r.constructor_rank > r.grid_pos) reasons.push({ label: 'Weaker constructor form', kind: 'neg' })
    }
  }

  const gained = r.grid_pos - r.rank
  if (gained > 0) return reasons.filter(x => x.kind === 'pos')
  if (gained < 0) return reasons.filter(x => x.kind === 'neg')
  return reasons
}

export interface SignalLine {
  label: string
  value: string
}

/** Compact, human-readable signal read-out for the "Why the Prediction?" bridge. */
export function signalSummary(r: PredictionRow): SignalLine[] {
  const lines: SignalLine[] = [{ label: 'Qualifying', value: `P${r.grid_pos}` }]
  if (r.stage2_used) {
    if (r.fp2_pace_rank != null) lines.push({ label: 'Weekend pace', value: `P${r.fp2_pace_rank}` })
    if (r.championship_rank != null) lines.push({ label: 'Championship', value: `P${r.championship_rank}` })
    if (r.constructor_rank != null) lines.push({ label: 'Constructor', value: `P${r.constructor_rank}` })
  }
  return lines
}

/** One-sentence, data-honest summary of a driver's predicted movement. */
export function predictionSentence(r: PredictionRow): string {
  const gained = r.grid_pos - r.rank
  const plural = (n: number) => (Math.abs(n) === 1 ? 'position' : 'positions')
  const move =
    gained > 0 ? `gain ${gained} ${plural(gained)}`
    : gained < 0 ? `lose ${Math.abs(gained)} ${plural(gained)}`
    : `hold P${r.rank}`
  const pos = driverReasons(r).filter(x => x.kind === 'pos').map(x => x.label.toLowerCase())
  const because = pos.length ? ` on the strength of ${pos.slice(0, 2).join(' and ')}` : ''
  return `The model expects ${r.driver} to ${move} from the grid${because}.`
}
