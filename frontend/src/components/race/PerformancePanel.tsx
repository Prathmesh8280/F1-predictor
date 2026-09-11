import type { PredictionResponse, PredictionRow } from '../../types'
import { driverDisplay } from '../../constants/drivers'

interface Props {
  data: PredictionResponse
}

function Metric({ n, d, label, sub }: { n: number; d: number; label: string; sub: string }) {
  return (
    <div className="bg-ground border border-border rounded-xl p-3 text-center">
      <div className="flex items-baseline justify-center gap-0.5">
        <span className="font-data font-bold text-xl text-ink">{n}</span>
        <span className="font-data text-sm text-muted">/{d}</span>
      </div>
      <span className="font-label font-semibold text-[9px] tracking-widest uppercase text-muted mt-1 block leading-tight">
        {label}
      </span>
      <span className="font-body text-[10px] text-muted mt-0.5 block leading-tight">
        {sub}
      </span>
    </div>
  )
}

export default function PerformancePanel({ data }: Props) {
  const completed: PredictionRow[] = data.predictions.filter(p => p.actual_rank != null)
  const N = completed.length

  if (N === 0) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-6">
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted">
          Race results not yet available.
        </p>
      </div>
    )
  }

  const exact = completed.filter(r => r.rank === r.actual_rank!).length
  const withinOne = completed.filter(r => Math.abs(r.rank - r.actual_rank!) <= 1).length
  const actualTop3 = new Set(completed.filter(r => r.actual_rank! <= 3).map(r => r.driver))
  const podiumHits = completed.filter(r => r.rank <= 3 && actualTop3.has(r.driver)).length

  const actualWinner = completed.find(r => r.actual_rank === 1)
  const winnerCorrect = actualWinner != null && actualWinner.rank === 1

  const withErr = completed
    .map(r => ({ row: r, err: Math.abs(r.rank - r.actual_rank!) }))
    .sort((a, b) => a.err - b.err)
  const bestCall = withErr[0]
  const biggestMiss = withErr[withErr.length - 1]

  return (
    <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col gap-6">

      {/* Header */}
      <div>
        <span className="inline-block font-label font-semibold text-[9px] tracking-widest uppercase text-accent bg-accent/8 px-2.5 py-1 rounded-full mb-3">
          Prediction Accuracy
        </span>
        <h2 className="font-display font-black text-2xl text-ink tracking-tight uppercase leading-tight">
          How Did We Do?
        </h2>
      </div>

      {/* Prediction hits */}
      <div>
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-3">
          Prediction Hits
        </p>
        <div className="grid grid-cols-3 gap-3">
          <Metric n={exact} d={N} label="Exact" sub="Right position" />
          <Metric n={withinOne} d={N} label="Within ±1" sub="Off by 1 or less" />
          <Metric n={podiumHits} d={3} label="Podium" sub="Top 3 correct" />
        </div>
      </div>

      {/* Winner row */}
      <div
        className={`flex items-center gap-3 rounded-xl px-4 py-3 ${
          winnerCorrect
            ? 'bg-positive/5 border border-positive/20'
            : 'bg-negative/5 border border-negative/20'
        }`}
      >
        <span
          className={`font-data font-bold text-xl shrink-0 ${
            winnerCorrect ? 'text-positive' : 'text-negative'
          }`}
        >
          {winnerCorrect ? '✓' : '✕'}
        </span>
        <div>
          <p
            className={`font-label font-bold text-[10px] tracking-widest uppercase ${
              winnerCorrect ? 'text-positive' : 'text-negative'
            }`}
          >
            Winner {winnerCorrect ? 'Correct' : 'Missed'}
          </p>
          {actualWinner && (
            <p className="font-body text-xs text-muted mt-0.5">
              {winnerCorrect
                ? `We predicted ${driverDisplay(actualWinner.driver)} to win — and they did.`
                : `We had ${driverDisplay(actualWinner.driver)} finishing P${actualWinner.rank} — they won instead.`}
            </p>
          )}
        </div>
      </div>

      <div className="border-t border-border" />

      {/* Best call + Biggest miss */}
      <div className="grid grid-cols-2 gap-5">
        {bestCall && (
          <div>
            <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-positive mb-2">
              Best Call
            </p>
            <p className="font-display font-black text-xl text-ink uppercase tracking-tight leading-none">
              {driverDisplay(bestCall.row.driver)}
            </p>
            <p className="font-body text-xs text-muted mt-1.5">
              {bestCall.err === 0
                ? `Predicted P${bestCall.row.rank}, finished P${bestCall.row.actual_rank}. Spot on.`
                : `Predicted P${bestCall.row.rank}, finished P${bestCall.row.actual_rank}. Just ${bestCall.err} place off.`}
            </p>
          </div>
        )}

        {biggestMiss && biggestMiss.err > 0 && (
          <div>
            <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-negative mb-2">
              Biggest Miss
            </p>
            <p className="font-display font-black text-xl text-ink uppercase tracking-tight leading-none">
              {driverDisplay(biggestMiss.row.driver)}
            </p>
            <p className="font-body text-xs text-muted mt-1.5">
              Predicted P{biggestMiss.row.rank}, finished P{biggestMiss.row.actual_rank}. A {biggestMiss.err}-place swing.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
