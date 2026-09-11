import type { PredictionRow } from '../../types'

interface PostRaceSummaryProps {
  predictions: PredictionRow[]
}

function errorFor(row: PredictionRow): number | null {
  if (row.actual_rank == null) return null
  return Math.abs(row.rank - row.actual_rank)
}

export default function PostRaceSummary({ predictions }: PostRaceSummaryProps) {
  const completed = predictions.filter(p => p.actual_rank != null)
  if (completed.length === 0) return null

  const withErr = completed
    .map(r => ({ row: r, err: errorFor(r) ?? 999 }))
    .sort((a, b) => a.err - b.err)

  const bestCall = withErr[0]
  const biggestMiss = withErr[withErr.length - 1]

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
      {/* Divider + header */}
      <div className="border-t-4 border-ink/10 pt-10 mb-8">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-muted mb-2">
          Race Completed
        </p>
        <h2 className="font-display font-black text-2xl sm:text-3xl text-ink tracking-tight">
          HOW DID WE DO?
        </h2>
        <p className="font-body text-sm text-muted mt-2">
          The race has finished. Here's how the prediction compared to the actual result.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Best Call */}
        {bestCall && (
          <div className="bg-positive/5 border border-positive/20 rounded-xl p-5">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-positive mb-3">
              Best Call
            </p>
            <p className="font-display font-black text-2xl text-ink mb-3">
              {bestCall.row.driver.toUpperCase()}
            </p>
            <dl className="space-y-1 mb-3">
              <div className="flex justify-between">
                <dt className="font-label text-xs text-muted">Predicted</dt>
                <dd className="font-data font-semibold text-sm text-ink">P{bestCall.row.rank}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="font-label text-xs text-muted">Actual</dt>
                <dd className="font-data font-semibold text-sm text-ink">P{bestCall.row.actual_rank}</dd>
              </div>
            </dl>
            <p
              className="font-label font-bold text-sm text-positive"
            >
              {bestCall.err === 0 ? 'EXACT PREDICTION' : `${bestCall.err}-place error`}
            </p>
          </div>
        )}

        {/* Biggest Miss */}
        {biggestMiss && biggestMiss.err > 0 && (
          <div className="bg-negative/5 border border-negative/20 rounded-xl p-5">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-negative mb-3">
              Biggest Miss
            </p>
            <p className="font-display font-black text-2xl text-ink mb-3">
              {biggestMiss.row.driver.toUpperCase()}
            </p>
            <dl className="space-y-1 mb-3">
              <div className="flex justify-between">
                <dt className="font-label text-xs text-muted">Predicted</dt>
                <dd className="font-data font-semibold text-sm text-ink">P{biggestMiss.row.rank}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="font-label text-xs text-muted">Actual</dt>
                <dd className="font-data font-semibold text-sm text-ink">P{biggestMiss.row.actual_rank}</dd>
              </div>
            </dl>
            <p className="font-label font-bold text-sm text-negative">
              {biggestMiss.err}-place error
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
