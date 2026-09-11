import type { PredictionResponse, PredictionRow, RaceEntry } from '../../types'
import { driverDisplay } from '../../constants/drivers'

export type LastRaceStatus =
  | { phase: 'idle' }
  | { phase: 'loading' }
  | { phase: 'loaded'; data: PredictionResponse }
  | { phase: 'error' }

interface LastRaceCardProps {
  previousRace: RaceEntry | null
  status: LastRaceStatus
  onViewFullReview: () => void
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="animate-pulse space-y-5">
      <div className="h-3 bg-border rounded w-1/3" />
      <div className="h-5 bg-border rounded w-2/3" />
      <div className="h-px bg-border" />
      <div className="grid grid-cols-3 gap-3">
        {[0, 1, 2].map(i => (
          <div key={i} className="space-y-2">
            <div className="h-7 bg-border rounded" />
            <div className="h-3 bg-border rounded w-2/3" />
          </div>
        ))}
      </div>
      <div className="h-px bg-border" />
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="h-3 bg-border rounded w-1/3" />
          <div className="h-4 bg-border rounded w-2/3" />
          <div className="h-3 bg-border rounded w-1/2" />
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-border rounded w-1/3" />
          <div className="h-4 bg-border rounded w-2/3" />
          <div className="h-3 bg-border rounded w-1/2" />
        </div>
      </div>
    </div>
  )
}

// ─── Metric block ─────────────────────────────────────────────────────────────

function Metric({
  numerator,
  denominator,
  label,
}: {
  numerator: number
  denominator: number
  label: string
}) {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="flex items-baseline gap-0.5">
        <span className="font-data font-bold text-2xl text-ink">{numerator}</span>
        <span className="font-data text-sm text-muted">/{denominator}</span>
      </div>
      <span className="font-label font-semibold text-[9px] tracking-widest uppercase text-muted mt-1 leading-tight">
        {label}
      </span>
    </div>
  )
}

// ─── Content when data is available ──────────────────────────────────────────

function LoadedContent({ data }: { data: PredictionResponse }) {
  // Only drivers with confirmed actual results contribute to metrics.
  const completed: PredictionRow[] = data.predictions.filter(
    p => p.actual_rank != null,
  )
  const N = completed.length

  if (N === 0) {
    return (
      <div className="space-y-1">
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted">
          Prediction Hits
        </p>
        <p className="font-body text-sm text-muted">
          Waiting for official race results.
        </p>
      </div>
    )
  }

  // ── Metrics ──────────────────────────────────────────────────────────────

  const exact = completed.filter(r => r.rank === r.actual_rank!).length

  const withinOne = completed.filter(
    r => Math.abs(r.rank - r.actual_rank!) <= 1,
  ).length

  const actualTop3 = new Set(
    completed.filter(r => r.actual_rank! <= 3).map(r => r.driver),
  )
  const podiumHits = completed.filter(
    r => r.rank <= 3 && actualTop3.has(r.driver),
  ).length

  const actualWinner = completed.find(r => r.actual_rank === 1)
  const winnerCorrect = actualWinner != null && actualWinner.rank === 1

  // ── Best call / biggest miss ──────────────────────────────────────────────

  const withErr = completed
    .map(r => ({ row: r, err: Math.abs(r.rank - r.actual_rank!) }))
    .sort((a, b) => a.err - b.err)
  const bestCall = withErr[0]
  const biggestMiss = withErr[withErr.length - 1]

  const modelMae = data.model_mae
  const baselineMae = data.baseline_mae

  return (
    <div className="space-y-5">

      {/* ── Prediction Hits ──────────────────────────────────────────────── */}
      <div>
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-3">
          Prediction Hits
        </p>
        <div className="grid grid-cols-3 gap-2">
          <Metric numerator={exact} denominator={N} label="Exact" />
          <Metric numerator={withinOne} denominator={N} label="Within ±1" />
          <Metric numerator={podiumHits} denominator={3} label="Podium" />
        </div>
      </div>

      {/* ── Winner ───────────────────────────────────────────────────────── */}
      <div
        className={`flex items-center gap-2 rounded-lg px-3 py-2 ${
          winnerCorrect ? 'bg-positive/8' : 'bg-negative/8'
        }`}
      >
        <span
          className={`font-data font-bold text-base ${
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

      <div className="border-t border-border" />

      {/* ── Best call / biggest miss ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4">
        {bestCall && (
          <div>
            <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-positive mb-1.5">
              Best Call
            </p>
            <p className="font-data font-bold text-sm text-ink leading-tight uppercase">
              {driverDisplay(bestCall.row.driver)}
            </p>
            <p className="font-body text-xs text-muted mt-0.5">
              P{bestCall.row.rank} → P{bestCall.row.actual_rank}
            </p>
            {bestCall.err === 0 ? (
              <span className="font-label font-semibold text-[9px] uppercase tracking-wide text-positive">
                exact
              </span>
            ) : (
              <span className="font-label font-semibold text-[9px] uppercase tracking-wide text-muted">
                {bestCall.err} {bestCall.err === 1 ? 'position' : 'positions'}
              </span>
            )}
          </div>
        )}

        {biggestMiss && biggestMiss.err > 0 && (
          <div>
            <p className="font-label font-semibold text-[9px] tracking-widest uppercase text-negative mb-1.5">
              Biggest Miss
            </p>
            <p className="font-data font-bold text-sm text-ink leading-tight uppercase">
              {driverDisplay(biggestMiss.row.driver)}
            </p>
            <p className="font-body text-xs text-muted mt-0.5">
              P{biggestMiss.row.rank} → P{biggestMiss.row.actual_rank}
            </p>
            <span className="font-label font-semibold text-[9px] uppercase tracking-wide text-negative">
              {biggestMiss.err} {biggestMiss.err === 1 ? 'position' : 'positions'}
            </span>
          </div>
        )}
      </div>

    </div>
  )
}

// ─── Main export ──────────────────────────────────────────────────────────────

export default function LastRaceCard({
  previousRace,
  status,
  onViewFullReview,
}: LastRaceCardProps) {
  if (!previousRace) {
    return (
      <div className="bg-surface border border-border rounded-xl p-6">
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-4">
          Last Race
        </p>
        <p className="font-body text-sm text-muted">
          No previous race — this is the first race of the season.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-6 flex flex-col">
      {/* Card header */}
      <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-2">
        Last Race
      </p>
      <p className="font-display font-bold text-base text-ink uppercase leading-tight mb-1">
        {previousRace.name} Grand Prix
      </p>
      <p className="font-label text-[11px] font-semibold tracking-widest uppercase text-muted mb-5">
        2026 Season
      </p>

      <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-ink mb-4">
        How did we do?
      </p>

      <div className="flex-1">
        {status.phase === 'loading' && <Skeleton />}

        {status.phase === 'error' && (
          <p className="font-body text-sm text-muted">
            Previous race performance is unavailable right now.
          </p>
        )}

        {status.phase === 'loaded' && <LoadedContent data={status.data} />}
      </div>

      {/* CTA */}
      <button
        onClick={onViewFullReview}
        disabled={status.phase === 'loading' || status.phase === 'error'}
        className="mt-6 w-full font-label font-bold text-sm tracking-widest uppercase text-accent
                   border border-accent/30 rounded-lg py-3 hover:bg-accent/5 transition-colors
                   disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-accent"
      >
        View Full Race Review →
      </button>
    </div>
  )
}
