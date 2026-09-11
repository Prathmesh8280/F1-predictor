import { useState } from 'react'
import type { PredictionRow } from '../../types'
import { movers, driverReasons } from '../../lib/predictionSignals'
import type { Mover } from '../../lib/predictionSignals'

interface BiggestMoversProps {
  predictions: PredictionRow[]
}

interface MoverDetailProps {
  mover: Mover
  onClose: () => void
}

function MoverDetail({ mover, onClose }: MoverDetailProps) {
  const { row, delta } = mover
  const reasons = driverReasons(row)
  const gained = delta > 0

  return (
    <div className="mt-2 mb-3 bg-ground border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-display font-bold text-sm tracking-tight text-ink">
          {row.driver.toUpperCase()}
        </h4>
        <button
          onClick={onClose}
          className="font-label text-xs text-muted hover:text-ink transition-colors focus-visible:outline-accent"
          aria-label="Close detail"
        >
          ✕
        </button>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mb-3">
        <dt className="font-label text-xs text-muted">Grid</dt>
        <dd className="font-data font-semibold text-xs text-ink">P{row.grid_pos}</dd>
        <dt className="font-label text-xs text-muted">Predicted</dt>
        <dd className="font-data font-semibold text-xs text-ink">P{row.rank}</dd>
        <dt className="font-label text-xs text-muted">Movement</dt>
        <dd
          className="font-data font-semibold text-xs"
          style={{ color: gained ? '#16a34a' : '#dc2626' }}
        >
          {gained ? '+' : ''}{delta}
        </dd>
      </dl>

      {reasons.length > 0 && (
        <>
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-2">Why?</p>
          <ul className="space-y-1">
            {reasons.map((r, i) => (
              <li key={i} className="font-body text-xs text-ink flex items-center gap-2">
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: r.kind === 'pos' ? '#16a34a' : '#dc2626' }}
                  aria-hidden="true"
                />
                {r.label}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

interface MoverRowProps {
  mover: Mover
  isExpanded: boolean
  onToggle: () => void
}

function MoverRow({ mover, isExpanded, onToggle }: MoverRowProps) {
  const { row, delta } = mover
  const gained = delta > 0

  return (
    <div>
      <button
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-label={`${row.driver} moved ${gained ? 'up' : 'down'} ${Math.abs(delta)} positions. Click to see details.`}
        className="w-full flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-ground transition-colors focus-visible:outline-accent text-left"
      >
        <div className="flex items-center gap-3">
          <span
            className="font-data font-bold text-sm"
            style={{ color: gained ? '#16a34a' : '#dc2626' }}
            aria-hidden="true"
          >
            {gained ? '↑' : '↓'}
          </span>
          <div>
            <span className="font-label font-semibold text-sm text-ink block leading-tight">
              {row.driver.toUpperCase()}
            </span>
            <span className="font-label text-xs text-muted">{row.team}</span>
          </div>
        </div>
        <span
          className="font-data font-bold text-base"
          style={{ color: gained ? '#16a34a' : '#dc2626' }}
        >
          {gained ? '+' : ''}{delta}
        </span>
      </button>
      {isExpanded && (
        <MoverDetail mover={mover} onClose={onToggle} />
      )}
    </div>
  )
}

export default function BiggestMovers({ predictions }: BiggestMoversProps) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const { gainers, losers } = movers(predictions, 4)

  const toggle = (driver: string) => setExpanded(v => v === driver ? null : driver)

  const hasMovers = gainers.length > 0 || losers.length > 0

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Position Changes
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          PREDICTED POSITION CHANGES
        </h2>
        <p className="font-body text-xs text-muted mt-1">
          Grid → predicted movement before the race.
        </p>
      </div>

      {!hasMovers ? (
        <p className="font-body text-sm text-muted">
          No significant position changes predicted. The grid order is largely maintained.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Gainers */}
          <div>
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-positive mb-3 px-3">
              Gainers
            </p>
            {gainers.length === 0 ? (
              <p className="font-body text-sm text-muted px-3">No significant gainers.</p>
            ) : (
              <div>
                {gainers.map(m => (
                  <MoverRow
                    key={m.row.driver}
                    mover={m}
                    isExpanded={expanded === m.row.driver}
                    onToggle={() => toggle(m.row.driver)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Losers */}
          <div>
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-negative mb-3 px-3">
              Losers
            </p>
            {losers.length === 0 ? (
              <p className="font-body text-sm text-muted px-3">No significant losers.</p>
            ) : (
              <div>
                {losers.map(m => (
                  <MoverRow
                    key={m.row.driver}
                    mover={m}
                    isExpanded={expanded === m.row.driver}
                    onToggle={() => toggle(m.row.driver)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
