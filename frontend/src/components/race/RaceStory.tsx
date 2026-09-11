import type { PredictionRow } from '../../types'
import TeamBadge from '../ui/TeamBadge'
import { driverDisplay } from '../../constants/drivers'

interface RaceStoryProps {
  predictions: PredictionRow[]
}

interface StoryEntry {
  row: PredictionRow
  err: number
}

function DriverCard({ row, err }: { row: PredictionRow; err: number }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <TeamBadge team={row.team} className="w-5 h-5 rounded-sm" />
        <span className="font-label font-semibold text-sm text-ink">{driverDisplay(row.driver)}</span>
        <span className="font-data text-[10px] text-muted">{row.driver.toUpperCase()}</span>
      </div>
      <p className="font-body text-xs text-muted">
        P{row.rank} predicted → P{row.actual_rank} actual
      </p>
      {err === 0 && (
        <span className="inline-block mt-1.5 font-label text-[10px] tracking-widest uppercase text-positive font-semibold">
          Exact
        </span>
      )}
      {err >= 3 && (
        <span className="inline-block mt-1.5 font-label text-[10px] tracking-widest uppercase text-negative font-semibold">
          {err}-place error
        </span>
      )}
    </div>
  )
}

export default function RaceStory({ predictions }: RaceStoryProps) {
  const completed = predictions.filter(p => p.actual_rank != null)
  if (completed.length === 0) return null

  const withErr: StoryEntry[] = completed
    .map(r => ({ row: r, err: Math.abs(r.rank - (r.actual_rank ?? r.rank)) }))
    .sort((a, b) => a.err - b.err)

  const nailed   = withErr.filter(e => e.err <= 1)
  const missed   = withErr.filter(e => e.err >= 3)
  const notable  = withErr.filter(e => e.err === 2)

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Analysis
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          RACE STORY
        </h2>
      </div>

      <div className="space-y-8">
        {nailed.length > 0 && (
          <div>
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-positive mb-4">
              The model got this right
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {nailed.map(({ row, err }) => (
                <DriverCard key={row.driver} row={row} err={err} />
              ))}
            </div>
          </div>
        )}

        {missed.length > 0 && (
          <div>
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-negative mb-4">
              The model missed this
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {missed.map(({ row, err }) => (
                <DriverCard key={row.driver} row={row} err={err} />
              ))}
            </div>
          </div>
        )}

        {notable.length > 0 && (
          <div>
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-muted mb-4">
              Other notable calls
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {notable.map(({ row, err }) => (
                <DriverCard key={row.driver} row={row} err={err} />
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
