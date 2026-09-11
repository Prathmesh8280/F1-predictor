import { useEffect, useMemo, useState } from 'react'
import type { PredictionRow } from '../../types'
import TeamBadge from '../ui/TeamBadge'
import { driverDisplay } from '../../constants/drivers'
import { useInView } from '../../hooks/useInView'

interface PredictionTableProps {
  predictions: PredictionRow[]
}

const ROW_H = 49
const SLIDE_MS = 2600
const STAGGER_MS = 140
const STAGGER_CAP = 1800

const COLOR_GAIN = '#16a34a'
const COLOR_LOSS = '#dc2626'

function prefersReducedMotion() {
  return typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

function DeltaCell({ delta }: { delta: number }) {
  if (delta === 0) return <span className="font-data text-xs text-muted">—</span>
  const up = delta > 0
  return (
    <span
      className="font-data font-semibold text-xs flex items-center gap-0.5"
      style={{ color: up ? COLOR_GAIN : COLOR_LOSS }}
      aria-label={`${up ? 'Gained' : 'Lost'} ${Math.abs(delta)} ${Math.abs(delta) === 1 ? 'position' : 'positions'}`}
    >
      {up ? '↑' : '↓'} {Math.abs(delta)}
    </span>
  )
}

function ExpandedRow({ row }: { row: PredictionRow }) {
  const signals: { label: string; value: string }[] = []

  if (row.championship_rank != null) {
    signals.push({ label: 'Championship', value: `#${row.championship_rank}` })
  }
  if (row.constructor_rank != null) {
    signals.push({ label: 'Constructor', value: `#${row.constructor_rank}` })
  }
  if (row.fp2_pace_rank != null) {
    signals.push({ label: 'Weekend pace', value: `P${row.fp2_pace_rank}` })
  }

  return (
    <div className="px-4 sm:px-6 py-4 bg-ground/50 border-t border-border">
      <dl className="flex flex-wrap gap-x-6 gap-y-2">
        <div>
          <dt className="font-label text-[10px] tracking-widest uppercase text-muted">Grid</dt>
          <dd className="font-data font-semibold text-sm text-ink">P{row.grid_pos}</dd>
        </div>
        <div>
          <dt className="font-label text-[10px] tracking-widest uppercase text-muted">Predicted</dt>
          <dd className="font-data font-semibold text-sm text-ink">P{row.rank}</dd>
        </div>
        {signals.length > 0 && (
          <>
            <div className="w-full border-t border-border pt-2 mt-1">
              <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-2">
                Model Signals
              </p>
              <dl className="flex flex-wrap gap-x-6 gap-y-1.5">
                {signals.map(s => (
                  <div key={s.label}>
                    <dt className="font-label text-[10px] tracking-widest uppercase text-muted">{s.label}</dt>
                    <dd className="font-data font-semibold text-sm text-ink">{s.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </>
        )}
      </dl>
    </div>
  )
}

export default function PredictionTable({ predictions }: PredictionTableProps) {
  const [expanded, setExpanded] = useState<number | null>(null)
  const sorted = useMemo(() => [...predictions].sort((a, b) => a.rank - b.rank), [predictions])

  const gridIndexOf = useMemo(() => {
    const byGrid = [...predictions].sort((a, b) => a.grid_pos - b.grid_pos)
    const map = new Map<string, number>()
    byGrid.forEach((row, i) => map.set(row.driver, i))
    return map
  }, [predictions])

  const [wrapRef, inView] = useInView<HTMLDivElement>()
  const [settled, setSettled] = useState(() => prefersReducedMotion())

  useEffect(() => {
    if (!inView) return
    if (prefersReducedMotion()) { setSettled(true); return }
    setSettled(false)
    let inner = 0
    const outer = requestAnimationFrame(() => {
      inner = requestAnimationFrame(() => setSettled(true))
    })
    return () => { cancelAnimationFrame(outer); if (inner) cancelAnimationFrame(inner) }
  }, [inView, sorted])

  const toggle = (rank: number) => {
    if (!settled) return
    setExpanded(v => v === rank ? null : rank)
  }

  return (
    <section id="full-order" className="scroll-mt-20 max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div ref={wrapRef} className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Full Prediction
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          PREDICTED RACE ORDER
        </h2>
        <p className="font-body text-sm text-muted mt-1">
          Click any row to see model signals.
        </p>
      </div>

      {/* Desktop table — each row group is its own <tbody> so we can transform it */}
      <div className="hidden sm:block bg-surface border border-border rounded-xl overflow-hidden">
        <table className="w-full" role="table">
          <thead>
            <tr className="border-b border-border bg-ground/50">
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">POS</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Driver</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Team</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Grid</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Change</th>
            </tr>
          </thead>
          {sorted.map((row, predIndex) => {
            const gridIndex = gridIndexOf.get(row.driver) ?? predIndex
            const offset = (gridIndex - predIndex) * ROW_H
            const delta = row.grid_pos - row.rank
            const delay = Math.min(predIndex * STAGGER_MS, STAGGER_CAP)
            const isExpanded = settled && expanded === row.rank
            const gaining = delta > 0
            const losing = delta < 0

            return (
              <tbody
                key={row.driver}
                style={{
                  transform: settled ? 'translateY(0)' : `translateY(${offset}px)`,
                  transition: `transform ${SLIDE_MS}ms cubic-bezier(0.16, 1, 0.3, 1)`,
                  transitionDelay: `${delay}ms`,
                  willChange: 'transform',
                }}
              >
                <tr
                  className={`border-b border-border transition-colors ${settled ? 'cursor-pointer hover:bg-ground/60' : ''} ${isExpanded ? 'bg-ground/40' : ''}`}
                  onClick={() => toggle(row.rank)}
                  aria-expanded={isExpanded}
                  role="button"
                  tabIndex={settled ? 0 : -1}
                  onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && toggle(row.rank)}
                  aria-label={`${row.driver}, predicted position ${row.rank}. Press to expand details.`}
                >
                  <td className="px-4 py-3">
                    <span
                      className="font-data font-bold text-base"
                      style={{ color: gaining ? COLOR_GAIN : losing ? COLOR_LOSS : undefined }}
                    >
                      {String(row.rank).padStart(2, '0')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-baseline gap-2">
                      <span className="font-label font-semibold text-sm text-ink">{driverDisplay(row.driver)}</span>
                      <span className="font-data text-[10px] text-muted">{row.driver.toUpperCase()}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <TeamBadge team={row.team} className="w-4 h-4 rounded-sm" />
                      <span className="font-label text-sm text-muted">{row.team}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-data text-sm text-muted">P{row.grid_pos}</span>
                  </td>
                  <td className="px-4 py-3">
                    <DeltaCell delta={delta} />
                  </td>
                </tr>
                {isExpanded && (
                  <tr>
                    <td colSpan={5} className="p-0">
                      <ExpandedRow row={row} />
                    </td>
                  </tr>
                )}
              </tbody>
            )
          })}
        </table>
      </div>

      {/* Mobile cards */}
      <div className="sm:hidden bg-surface border border-border rounded-xl overflow-hidden">
        {sorted.map((row, predIndex) => {
          const gridIndex = gridIndexOf.get(row.driver) ?? predIndex
          const offset = (gridIndex - predIndex) * ROW_H
          const delta = row.grid_pos - row.rank
          const delay = Math.min(predIndex * STAGGER_MS, STAGGER_CAP)
          const isExpanded = settled && expanded === row.rank
          const gaining = delta > 0
          const losing = delta < 0

          return (
            <div
              key={row.driver}
              className="border-b border-border last:border-0"
              style={{
                transform: settled ? 'translateY(0)' : `translateY(${offset}px)`,
                transition: `transform ${SLIDE_MS}ms cubic-bezier(0.16, 1, 0.3, 1)`,
                transitionDelay: `${delay}ms`,
                willChange: 'transform',
              }}
            >
              <button
                onClick={() => toggle(row.rank)}
                disabled={!settled}
                aria-expanded={isExpanded}
                aria-label={`${row.driver}, P${row.rank}. Tap to expand.`}
                className="w-full flex items-center gap-4 px-4 py-3 hover:bg-ground/60 transition-colors focus-visible:outline-accent text-left"
              >
                <span
                  className="font-data font-bold text-xl w-8 flex-shrink-0"
                  style={{ color: gaining ? COLOR_GAIN : losing ? COLOR_LOSS : undefined }}
                >
                  {String(row.rank).padStart(2, '0')}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-label font-bold text-sm text-ink truncate">{driverDisplay(row.driver)}</span>
                    <span className="font-data text-[10px] text-muted shrink-0">{row.driver.toUpperCase()}</span>
                  </div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <TeamBadge team={row.team} className="w-3.5 h-3.5 rounded-sm" />
                    <span className="font-label text-xs text-muted">{row.team}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-0.5">
                  <span className="font-data text-xs text-muted">Grid P{row.grid_pos}</span>
                  <DeltaCell delta={delta} />
                </div>
              </button>
              {isExpanded && <ExpandedRow row={row} />}
            </div>
          )
        })}
      </div>
    </section>
  )
}
