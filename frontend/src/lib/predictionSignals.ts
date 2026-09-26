import type { PredictionRow } from '../types'
import { driverDisplay } from '../constants/drivers'

// All helpers here derive strictly from real model outputs on PredictionRow.
// Nothing is invented — a reason only appears when the underlying signal
// actually supports the predicted direction (spec §6, §32).

/** 1 → "1st", 2 → "2nd", 16 → "16th". */
export function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return `${n}${s[(v - 20) % 10] ?? s[v] ?? s[0]}`
}

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

export interface ReasonBlock {
  title: string
  body: string
}

/**
 * Up to three plain-language reasons behind the predicted winner's result,
 * each backed by a real signal on the row. Starting position always applies;
 * pace and season-form reasons appear only when those signals exist (e.g. not
 * on Round 1). Nothing is fabricated.
 */
export function winnerReasons(r: PredictionRow): ReasonBlock[] {
  const name = driverDisplay(r.driver)
  const blocks: ReasonBlock[] = []

  // 1 — Starting position (always available).
  let startBody: string
  if (r.grid_pos === 1) {
    startBody = `${name} starts from pole — the strongest starting position, with no cars ahead to overtake.`
  } else if (r.grid_pos <= 3) {
    startBody = `${name} starts ${ordinal(r.grid_pos)} on the grid, near the front and within reach of the lead.`
  } else {
    startBody = `${name} starts ${ordinal(r.grid_pos)}, and the model expects race pace to recover ground from there.`
  }
  blocks.push({ title: 'Starting Position', body: startBody })

  // 2 — Weekend pace (only when the FP2/Sprint signal exists).
  if (r.fp2_pace_rank != null) {
    const body = r.fp2_pace_rank <= 3
      ? `${r.team} showed strong long-run pace this weekend, ranking ${ordinal(r.fp2_pace_rank)} fastest.`
      : `${r.team}'s weekend long-run pace ranked ${ordinal(r.fp2_pace_rank)}, which the model factors in.`
    blocks.push({ title: 'Weekend Pace', body })
  }

  // 3 — Season form (only when standings exist).
  if (r.championship_rank != null || r.constructor_rank != null) {
    const parts: string[] = []
    if (r.championship_rank != null) parts.push(`${ordinal(r.championship_rank)} in the drivers' championship`)
    if (r.constructor_rank != null) parts.push(`${ordinal(r.constructor_rank)} among constructors`)
    const joined = parts.length === 2 ? `${parts[0]} and ${parts[1]}` : parts[0]
    blocks.push({ title: 'Season Form', body: `${name} sits ${joined}, reinforcing the prediction.` })
  }

  return blocks.slice(0, 3)
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
