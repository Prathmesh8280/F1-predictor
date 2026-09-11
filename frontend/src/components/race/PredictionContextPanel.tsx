import type { PredictionResponse } from '../../types'
import { movers, signalSummary } from '../../lib/predictionSignals'
import { driverDisplay } from '../../constants/drivers'

interface Props {
  data: PredictionResponse
}

export default function PredictionContextPanel({ data }: Props) {
  const { predictions } = data
  const { gainers, losers } = movers(predictions, 3)
  const winner = predictions.find(r => r.rank === 1)
  const signals = winner ? signalSummary(winner) : []

  return (
    <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col gap-6">

      {/* Header — matches PerformancePanel */}
      <div>
        <span className="inline-block font-label font-semibold text-[9px] tracking-widest uppercase text-accent bg-accent/8 px-2.5 py-1 rounded-full mb-3">
          Pre-Race
        </span>
        <h2 className="font-display font-black text-2xl text-ink tracking-tight uppercase leading-tight">
          What To Watch
        </h2>
      </div>

      {/* Gainers + Fallers — 2-column compact layout */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-positive mb-3">
            Gaining
          </p>
          <div className="space-y-2.5">
            {gainers.map(({ row, delta }) => (
              <div key={row.driver} className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-data font-bold text-sm text-positive shrink-0">↑</span>
                  <div className="min-w-0">
                    <p className="font-label font-semibold text-sm text-ink uppercase truncate leading-tight">
                      {driverDisplay(row.driver)}
                    </p>
                    <p className="font-label text-[10px] text-muted">
                      P{row.grid_pos}→P{row.rank}
                    </p>
                  </div>
                </div>
                <span className="font-data font-bold text-sm text-positive shrink-0 ml-2">
                  +{delta}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-negative mb-3">
            Dropping
          </p>
          <div className="space-y-2.5">
            {losers.map(({ row, delta }) => (
              <div key={row.driver} className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-data font-bold text-sm text-negative shrink-0">↓</span>
                  <div className="min-w-0">
                    <p className="font-label font-semibold text-sm text-ink uppercase truncate leading-tight">
                      {driverDisplay(row.driver)}
                    </p>
                    <p className="font-label text-[10px] text-muted">
                      P{row.grid_pos}→P{row.rank}
                    </p>
                  </div>
                </div>
                <span className="font-data font-bold text-sm text-negative shrink-0 ml-2">
                  {delta}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-border" />

      {/* Winner signals — compact, matches PerformancePanel's Best Call/Miss style */}
      {winner && (
        <div>
          <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-positive mb-3">
            Why {driverDisplay(winner.driver)}?
          </p>
          <dl className="space-y-2">
            {signals.map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
                <dt className="font-label font-semibold text-xs text-muted">{label}</dt>
                <dd className="font-data font-semibold text-xs text-ink">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  )
}
