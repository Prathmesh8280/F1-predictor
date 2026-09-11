import { useEffect, useMemo, useState } from 'react'
import type { PredictionRow } from '../../types'
import TeamBadge from '../ui/TeamBadge'
import { driverDisplay } from '../../constants/drivers'
import { useInView } from '../../hooks/useInView'

interface ActualVsPredictedProps {
  predictions: PredictionRow[]
}

const ROW_H = 49
const SLIDE_MS = 2600
const STAGGER_MS = 140
const STAGGER_CAP = 1800
const REVEAL_MS = 400
const REVEAL_LAG = 300

const COLOR_EXACT = '#16a34a'
const COLOR_CLOSE = '#d97706'
const COLOR_MISS  = '#dc2626'

function prefersReducedMotion() {
  return typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

function ErrorBadge({ err }: { err: number }) {
  const cls =
    err === 0 ? 'bg-positive/10 text-positive' :
    err <= 2  ? 'bg-warning/10 text-warning' :
                'bg-negative/10 text-negative'
  return (
    <span className={`inline-block font-data font-semibold text-xs px-2 py-0.5 rounded-full ${cls}`}>
      {err === 0 ? '✓' : `±${err}`}
    </span>
  )
}

export default function ActualVsPredicted({ predictions }: ActualVsPredictedProps) {
  // All hooks must come before any conditional return
  const completed = useMemo(
    () => predictions.filter(p => p.actual_rank != null),
    [predictions],
  )

  // Final display order: actual finishing positions (P1 → P22)
  const sorted = useMemo(
    () => [...completed].sort((a, b) => (a.actual_rank ?? 99) - (b.actual_rank ?? 99)),
    [completed],
  )

  // Opening positions: each driver's slot in predicted order
  const predIndexOf = useMemo(() => {
    const byPred = [...completed].sort((a, b) => a.rank - b.rank)
    const map = new Map<string, number>()
    byPred.forEach((row, i) => map.set(row.driver, i))
    return map
  }, [completed])

  const [wrapRef, inView] = useInView<HTMLDivElement>()
  const [settled, setSettled] = useState(() => prefersReducedMotion())

  useEffect(() => {
    if (!inView || completed.length === 0) return
    if (prefersReducedMotion()) { setSettled(true); return }
    setSettled(false)
    let inner = 0
    const outer = requestAnimationFrame(() => {
      inner = requestAnimationFrame(() => setSettled(true))
    })
    return () => { cancelAnimationFrame(outer); if (inner) cancelAnimationFrame(inner) }
  }, [inView, completed])

  // Safe to return early after all hooks
  if (completed.length === 0) return null

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div ref={wrapRef} className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Full Comparison
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          ACTUAL VS PREDICTED
        </h2>
        <p className="font-body text-sm text-muted mt-1">
          Rows start in predicted order and slide to where drivers actually finished.
        </p>
      </div>

      {/* Desktop table */}
      <div className="hidden sm:block bg-surface border border-border rounded-xl overflow-hidden">
        <table className="w-full" role="table">
          <thead>
            <tr className="border-b border-border bg-ground/50">
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Actual</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Driver</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Team</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Predicted</th>
              <th className="px-4 py-3 text-left font-label text-[10px] tracking-widest uppercase text-muted font-semibold">Error</th>
            </tr>
          </thead>
          {sorted.map((row, actualIndex) => {
            const predIndex = predIndexOf.get(row.driver) ?? actualIndex
            const offset = (predIndex - actualIndex) * ROW_H
            const delay = Math.min(actualIndex * STAGGER_MS, STAGGER_CAP)
            const err = Math.abs(row.rank - (row.actual_rank ?? row.rank))
            const errColor = err === 0 ? COLOR_EXACT : err <= 2 ? COLOR_CLOSE : COLOR_MISS
            const revealStyle = {
              opacity: settled ? 1 : 0,
              transition: `opacity ${REVEAL_MS}ms ease`,
              transitionDelay: `${delay + REVEAL_LAG}ms`,
            }

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
                <tr className="border-b border-border last:border-0">
                  <td className="px-4 py-3">
                    <span className="font-data font-bold text-base" style={{ color: errColor, ...revealStyle }}>
                      {String(row.actual_rank).padStart(2, '0')}
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
                    <span className="font-data text-sm text-muted">P{row.rank}</span>
                  </td>
                  <td className="px-4 py-3" style={revealStyle}>
                    <ErrorBadge err={err} />
                  </td>
                </tr>
              </tbody>
            )
          })}
        </table>
      </div>

      {/* Mobile cards */}
      <div className="sm:hidden bg-surface border border-border rounded-xl overflow-hidden">
        {sorted.map((row, actualIndex) => {
          const predIndex = predIndexOf.get(row.driver) ?? actualIndex
          const offset = (predIndex - actualIndex) * ROW_H
          const delay = Math.min(actualIndex * STAGGER_MS, STAGGER_CAP)
          const err = Math.abs(row.rank - (row.actual_rank ?? row.rank))
          const errColor = err === 0 ? COLOR_EXACT : err <= 2 ? COLOR_CLOSE : COLOR_MISS
          const revealStyle = {
            opacity: settled ? 1 : 0,
            transition: `opacity ${REVEAL_MS}ms ease`,
            transitionDelay: `${delay + REVEAL_LAG}ms`,
          }

          return (
            <div
              key={row.driver}
              className="flex items-center gap-4 px-4 py-3 border-b border-border last:border-0"
              style={{
                transform: settled ? 'translateY(0)' : `translateY(${offset}px)`,
                transition: `transform ${SLIDE_MS}ms cubic-bezier(0.16, 1, 0.3, 1)`,
                transitionDelay: `${delay}ms`,
                willChange: 'transform',
              }}
            >
              <span className="font-data font-bold text-xl w-8 flex-shrink-0" style={{ color: errColor, ...revealStyle }}>
                {String(row.actual_rank).padStart(2, '0')}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-1.5">
                  <span className="font-label font-semibold text-sm text-ink">{driverDisplay(row.driver)}</span>
                  <span className="font-data text-[10px] text-muted">{row.driver.toUpperCase()}</span>
                </div>
                <div className="flex items-center gap-1 mt-0.5">
                  <TeamBadge team={row.team} className="w-3.5 h-3.5 rounded-sm" />
                  <span className="font-label text-xs text-muted">{row.team}</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1" style={revealStyle}>
                <span className="font-data text-xs text-muted">Pred P{row.rank}</span>
                <ErrorBadge err={err} />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
