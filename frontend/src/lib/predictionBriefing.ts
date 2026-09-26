import type { PredictionRow, CircuitInfo } from '../types'
import { driverDisplay } from '../constants/drivers'
import { ordinal } from './predictionSignals'

const NUMBER_WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
const numberWord = (n: number): string => NUMBER_WORDS[n] ?? String(n)

/** The single driver the model expects to climb the most (grid → predicted). */
export function biggestGainer(predictions: PredictionRow[]): { row: PredictionRow; gain: number } | null {
  const movers = predictions
    .map(r => ({ row: r, gain: r.grid_pos - r.rank }))
    .filter(m => m.gain > 0)
    .sort((a, b) => b.gain - a.gain)
  return movers[0] ?? null
}

/** How many of the actual top-3 finishers the model also placed in its top 3. */
export function podiumHitCount(predictions: PredictionRow[]): number {
  const completed = predictions.filter(p => p.actual_rank != null)
  const actualTop3 = new Set(completed.filter(r => (r.actual_rank as number) <= 3).map(r => r.driver))
  return completed.filter(r => r.rank <= 3 && actualTop3.has(r.driver)).length
}

/** The driver with the largest gap between predicted and actual finish. */
export function biggestMiss(predictions: PredictionRow[]): { row: PredictionRow; err: number } | null {
  const withErr = predictions
    .filter(p => p.actual_rank != null)
    .map(r => ({ row: r, err: Math.abs(r.rank - (r.actual_rank as number)) }))
    .sort((a, b) => b.err - a.err)
  return withErr[0] ?? null
}

/** The driver the model predicted most accurately (smallest gap). */
export function bestCall(predictions: PredictionRow[]): { row: PredictionRow; err: number } | null {
  const withErr = predictions
    .filter(p => p.actual_rank != null)
    .map(r => ({ row: r, err: Math.abs(r.rank - (r.actual_rank as number)) }))
    .sort((a, b) => a.err - b.err)
  return withErr[0] ?? null
}

/**
 * Plain-language takeaway on how the model did — winner call, podium hits, and
 * biggest prediction swing. Derived entirely from real predicted vs actual
 * positions; reuses the shared podiumHitCount / biggestMiss utilities.
 */
export function resultVerdict(predictions: PredictionRow[]): string {
  const completed = predictions.filter(p => p.actual_rank != null)
  if (completed.length === 0) return ''

  const actualWinner = completed.find(p => p.actual_rank === 1)
  const ourP1 = [...predictions].sort((a, b) => a.rank - b.rank)[0]
  const calledWinner = !!actualWinner && !!ourP1 && actualWinner.driver === ourP1.driver
  const hits = podiumHitCount(predictions)
  const miss = biggestMiss(predictions)

  const parts: string[] = []
  if (calledWinner && actualWinner) {
    parts.push(`The model called ${driverDisplay(actualWinner.driver)} correctly and got ${hits} of the three podium finishers right.`)
  } else if (actualWinner && ourP1) {
    parts.push(`The model tipped ${driverDisplay(ourP1.driver)} to win, but ${driverDisplay(actualWinner.driver)} took it — it still got ${hits} of three podium finishers right.`)
  }
  if (miss && miss.err >= 3) {
    const dir = (miss.row.actual_rank as number) < miss.row.rank ? 'higher' : 'lower'
    parts.push(`Its biggest miss was ${driverDisplay(miss.row.driver)}, who finished ${miss.err} place${miss.err === 1 ? '' : 's'} ${dir} than predicted.`)
  }
  return parts.join(' ')
}

/**
 * A concise, editorial race story generated from real results only. Leads with
 * the winner (and whether we called it), then highlights the drivers who most
 * exceeded their predicted finish. No fabricated causes or race events.
 */
export function raceStoryNarrative(predictions: PredictionRow[]): string {
  const completed = predictions.filter(p => p.actual_rank != null)
  if (completed.length === 0) return ''

  const byActual = [...completed].sort((a, b) => (a.actual_rank as number) - (b.actual_rank as number))
  const winner = byActual[0]
  const ourP1 = [...predictions].sort((a, b) => a.rank - b.rank)[0]

  const parts: string[] = []

  // Winner — and whether we called it.
  if (winner) {
    const from = winner.grid_pos === 1 ? 'from pole' : `from ${ordinal(winner.grid_pos)} on the grid`
    parts.push(
      ourP1 && ourP1.driver === winner.driver
        ? `${driverDisplay(winner.driver)} won ${from}, matching our prediction.`
        : `${driverDisplay(winner.driver)} won ${from}; the model had tipped ${driverDisplay(ourP1.driver)}.`,
    )
  }

  // Podium surprises — P2/P3 finishers who beat their predicted finish.
  const podiumSurprises = [byActual[1], byActual[2]]
    .filter((p): p is PredictionRow => !!p && p.rank - (p.actual_rank as number) >= 2)

  if (podiumSurprises[0]) {
    const p = podiumSurprises[0]
    parts.push(`The standout was ${driverDisplay(p.driver)}, who finished ${ordinal(p.actual_rank as number)} after being predicted ${ordinal(p.rank)}.`)
  }
  if (podiumSurprises[1]) {
    const p = podiumSurprises[1]
    parts.push(`${driverDisplay(p.driver)} also exceeded expectations to take ${ordinal(p.actual_rank as number)}, from a predicted ${ordinal(p.rank)}.`)
  }

  // One notable miss — a driver predicted well up the order who dropped sharply.
  const miss = biggestMiss(predictions)
  if (miss && miss.err >= 5 && (miss.row.actual_rank as number) > miss.row.rank) {
    parts.push(`${driverDisplay(miss.row.driver)}, predicted ${ordinal(miss.row.rank)}, finished ${ordinal(miss.row.actual_rank as number)}.`)
  }

  return parts.join(' ')
}

/** One compact editorial line about the standout climber — real data only. */
export function keyStoryLine(predictions: PredictionRow[]): string {
  const top = biggestGainer(predictions)
  if (!top) return ''
  const name = driverDisplay(top.row.driver)
  if (top.row.championship_rank === 1) {
    return `Championship leader ${name} starts ${ordinal(top.row.grid_pos)}, but the model expects a ${numberWord(top.gain)}-place recovery to ${ordinal(top.row.rank)}.`
  }
  return `${name} is the model's biggest climber, tipped to gain ${numberWord(top.gain)} places from ${ordinal(top.row.grid_pos)} to ${ordinal(top.row.rank)}.`
}

// Plain-language read of a circuit's overtaking character. Keyed by the
// overtaking enum the API already returns — nothing here is invented.
const OVERTAKING_PHRASE: Record<CircuitInfo['overtaking'], string> = {
  'VERY HIGH': 'one of the easiest tracks to overtake on',
  'HIGH': 'an overtaking-friendly track',
  'MEDIUM': 'a track where starting position matters',
  'LOW': 'a track where passing is hard',
  'VERY LOW': 'a track where passing is very hard',
}

function listJoin(names: string[]): string {
  if (names.length <= 1) return names[0] ?? ''
  if (names.length === 2) return `${names[0]} and ${names[1]}`
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
}

/**
 * A short, editorial race briefing built strictly from real model outputs.
 * Every claim traces to a field on PredictionRow / CircuitInfo — no fabricated
 * storylines. Returns '' when there isn't enough data to say anything honest.
 */
export function raceBriefing(
  predictions: PredictionRow[],
  circuit: CircuitInfo,
): string {
  if (predictions.length === 0) return ''

  const byRank = [...predictions].sort((a, b) => a.rank - b.rank)
  const winner = byRank[0]
  if (!winner) return ''
  const pole = predictions.find(p => p.grid_pos === 1)

  // Sentence 1 — pole vs predicted winner.
  const winnerName = driverDisplay(winner.driver)
  const strongestCar = winner.constructor_rank === 1
  let s1: string
  if (pole && pole.driver === winner.driver) {
    s1 = `${winnerName} starts from pole and the model backs him to convert it`
    s1 += strongestCar
      ? `, with ${winner.team} rated the strongest car on the grid.`
      : '.'
  } else if (pole) {
    s1 = `${driverDisplay(pole.driver)} starts from pole, but the model tips ${winnerName} to take the win from P${winner.grid_pos}.`
  } else {
    s1 = `The model tips ${winnerName} to win from P${winner.grid_pos}.`
  }

  // Sentence 2 — is the front settled, or reshuffled?
  const top3 = byRank.slice(0, 3)
  const held = top3.filter(r => r.rank === r.grid_pos && r.driver !== winner.driver)
  let s2 = ''
  if (held.length >= 1) {
    s2 = `The front looks settled — ${listJoin(held.map(r => driverDisplay(r.driver)))} ${held.length === 1 ? 'is' : 'are'} predicted to hold station.`
  } else {
    s2 = 'The model reshuffles the top of the grid rather than leaving it as it qualified.'
  }

  // Sentence 3 — the standout climber.
  const movers = predictions
    .map(r => ({ r, gain: r.grid_pos - r.rank }))
    .filter(m => m.gain > 0)
    .sort((a, b) => b.gain - a.gain)
  const top = movers[0]
  let s3 = ''
  if (top) {
    const name = driverDisplay(top.r.driver)
    const places = `${top.gain} place${top.gain === 1 ? '' : 's'}`
    const otPhrase = OVERTAKING_PHRASE[circuit.overtaking] ?? 'this track'
    if (top.r.championship_rank === 1) {
      s3 = `The story sits further back: championship leader ${name} qualified only P${top.r.grid_pos}, and even on ${otPhrase} the model claws him back just ${places}, to P${top.r.rank}.`
    } else {
      s3 = `${name} is the model's biggest climber, tipped to gain ${places} from P${top.r.grid_pos} to P${top.r.rank}.`
    }
  }

  return [s1, s2, s3].filter(Boolean).join(' ')
}
