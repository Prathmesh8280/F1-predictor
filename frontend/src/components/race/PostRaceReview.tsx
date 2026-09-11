import type { PredictionResponse } from '../../types'
import { driverDisplay } from '../../constants/drivers'

interface PostRaceReviewProps {
  data: PredictionResponse
}

export default function PostRaceReview({ data }: PostRaceReviewProps) {
  const completed = data.predictions.filter(p => p.actual_rank != null)
  const N = completed.length
  if (N === 0) return null

  // ── Prediction Hits ──────────────────────────────────────────────────────────
  const exact = completed.filter(r => r.rank === r.actual_rank!).length
  const withinOne = completed.filter(r => Math.abs(r.rank - r.actual_rank!) <= 1).length
  const actualTop3 = new Set(completed.filter(r => r.actual_rank! <= 3).map(r => r.driver))
  const podiumHits = completed.filter(r => r.rank <= 3 && actualTop3.has(r.driver)).length
  const actualWinner = completed.find(r => r.actual_rank === 1)
  const winnerCorrect = actualWinner != null && actualWinner.rank === 1

  // ── Best Call / Biggest Miss ─────────────────────────────────────────────────
  const withErr = completed
    .map(r => ({ row: r, err: Math.abs(r.rank - r.actual_rank!) }))
    .sort((a, b) => a.err - b.err)
  const bestCall = withErr[0]
  const biggestMiss = withErr[withErr.length - 1]

  // ── Top-5 side-by-side comparison ────────────────────────────────────────────
  const TOP_N = 5
  const compRows = Array.from({ length: Math.min(TOP_N, N) }, (_, i) => {
    const pos = i + 1
    const predicted = data.predictions.find(r => r.rank === pos)
    const actual = completed.find(r => r.actual_rank === pos)
    const match = !!(predicted && actual && predicted.driver === actual.driver)
    return { pos, predicted, actual, match }
  })

  return (
    <>
      {/* ── Chapter header ───────────────────────────────────────────────────── */}
      <section className="border-t-4 border-ink/10 max-w-6xl mx-auto px-4 sm:px-6 pt-12 pb-8">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-2">
          Race Completed
        </p>
        <h2 className="font-display font-black text-3xl sm:text-4xl text-ink tracking-tight">
          HOW DID WE DO?
        </h2>
        <p className="font-body text-sm text-muted mt-2 max-w-lg">
          The race has finished. Here's how the prediction compared with the actual result.
        </p>
      </section>

      {/* ── Comparison + Hits ────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

          {/* Prediction vs Actual rows */}
          <div>
            <div className="grid grid-cols-[1fr_1.5rem_1fr] gap-x-2 px-3 mb-3">
              <span className="font-label font-semibold text-[9px] tracking-widest uppercase text-muted">
                Prediction
              </span>
              <span />
              <span className="font-label font-semibold text-[9px] tracking-widest uppercase text-muted text-right">
                Actual
              </span>
            </div>
            <div className="space-y-1.5">
              {compRows.map(({ pos, predicted, actual, match }) => (
                <div
                  key={pos}
                  className={`grid grid-cols-[1fr_1.5rem_1fr] gap-x-2 items-center px-3 py-3 rounded-xl border ${
                    match
                      ? 'bg-positive/5 border-positive/20'
                      : 'bg-surface border-border'
                  }`}
                >
                  <div className="min-w-0">
                    <span className="font-data text-[10px] text-muted block leading-none mb-0.5">
                      P{pos}
                    </span>
                    <span
                      className={`font-label font-bold text-sm uppercase truncate block leading-tight ${
                        match ? 'text-positive' : 'text-ink'
                      }`}
                    >
                      {predicted ? driverDisplay(predicted.driver) : '—'}
                    </span>
                  </div>
                  <span
                    className={`text-center text-sm leading-none ${
                      match ? 'text-positive font-bold' : 'text-muted'
                    }`}
                  >
                    {match ? '✓' : '→'}
                  </span>
                  <div className="text-right min-w-0">
                    <span className="font-data text-[10px] text-muted block leading-none mb-0.5">
                      P{pos}
                    </span>
                    <span
                      className={`font-label font-bold text-sm uppercase truncate block leading-tight ${
                        match ? 'text-positive' : 'text-ink'
                      }`}
                    >
                      {actual ? driverDisplay(actual.driver) : '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Prediction Hits */}
          <div className="space-y-4">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted">
              Prediction Hits
            </p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { n: exact,      d: N, label: 'Exact'     },
                { n: withinOne,  d: N, label: 'Within ±1' },
                { n: podiumHits, d: 3, label: 'Podium'    },
              ].map(({ n, d, label }) => (
                <div
                  key={label}
                  className="bg-surface border border-border rounded-xl p-4 text-center"
                >
                  <div className="flex items-baseline justify-center gap-0.5">
                    <span className="font-data font-bold text-2xl text-ink">{n}</span>
                    <span className="font-data text-sm text-muted">/{d}</span>
                  </div>
                  <span className="font-label font-semibold text-[9px] tracking-widest uppercase text-muted mt-1 block leading-tight">
                    {label}
                  </span>
                </div>
              ))}
            </div>

            <div
              className={`flex items-center gap-3 rounded-xl px-4 py-3.5 ${
                winnerCorrect
                  ? 'bg-positive/5 border border-positive/20'
                  : 'bg-negative/5 border border-negative/20'
              }`}
            >
              <span
                className={`font-data font-bold text-xl leading-none ${
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
                      ? `${driverDisplay(actualWinner.driver)} predicted P1`
                      : `${driverDisplay(actualWinner.driver)} predicted P${actualWinner.rank}`}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Editorial cards ───────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {bestCall && (
            <div className="bg-surface border border-positive/20 rounded-xl p-6">
              <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-positive mb-5">
                Best Call
              </p>
              <p className="font-display font-black text-2xl text-ink tracking-tight uppercase mb-5">
                {driverDisplay(bestCall.row.driver)}
              </p>
              <div className="flex items-center gap-3 mb-4">
                <span className="font-data font-bold text-xl text-muted">
                  P{bestCall.row.rank}
                </span>
                <span className="text-muted">→</span>
                <span className="font-data font-bold text-xl text-ink">
                  P{bestCall.row.actual_rank}
                </span>
              </div>
              <p className="font-label font-bold text-sm text-positive tracking-widest uppercase">
                {bestCall.err === 0 ? 'Exact Prediction' : `${bestCall.err}-Position Error`}
              </p>
            </div>
          )}

          {biggestMiss && biggestMiss.err > 0 && (
            <div className="bg-surface border border-negative/20 rounded-xl p-6">
              <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-negative mb-5">
                Biggest Miss
              </p>
              <p className="font-display font-black text-2xl text-ink tracking-tight uppercase mb-5">
                {driverDisplay(biggestMiss.row.driver)}
              </p>
              <div className="flex items-center gap-3 mb-4">
                <span className="font-data font-bold text-xl text-muted">
                  P{biggestMiss.row.rank}
                </span>
                <span className="text-muted">→</span>
                <span className="font-data font-bold text-xl text-ink">
                  P{biggestMiss.row.actual_rank}
                </span>
              </div>
              <p className="font-label font-bold text-sm text-negative tracking-widest uppercase">
                {biggestMiss.err}-Position Error
              </p>
            </div>
          )}
        </div>
      </section>
    </>
  )
}
