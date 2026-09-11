import { useEffect, useMemo, useState } from 'react'
import type { PredictionRow } from '../../types'
import { useInView } from '../../hooks/useInView'
import { driverDisplay } from '../../constants/drivers'

interface GridFlowVizProps {
  predictions: PredictionRow[]
}

const ROW_H = 44
const SLIDE_MS = 1800
const STAGGER_MS = 90
const STAGGER_CAP = 900
const REVEAL_MS = 400
const REVEAL_LAG = 300

const COLOR_GAIN = '#16a34a'
const COLOR_LOSS = '#dc2626'
const COLOR_NEUTRAL = '#9CA3AF'

function prefersReducedMotion() {
  return typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

export default function GridFlowViz({ predictions }: GridFlowVizProps) {
  const byPredicted = useMemo(
    () => [...predictions].sort((a, b) => a.rank - b.rank),
    [predictions],
  )

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
    if (prefersReducedMotion()) {
      setSettled(true)
      return
    }
    setSettled(false)
    let inner = 0
    const outer = requestAnimationFrame(() => {
      inner = requestAnimationFrame(() => setSettled(true))
    })
    return () => {
      cancelAnimationFrame(outer)
      if (inner) cancelAnimationFrame(inner)
    }
  }, [inView, byPredicted])

  return (
    <div ref={wrapRef}>
      <div className="mb-2">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Grid Visualization
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          FROM QUALIFYING TO PREDICTION
        </h2>
        <p className="font-body text-sm text-muted mt-1">
          See how the model reshuffles the starting grid.
        </p>
      </div>

      <div className="bg-surface border border-border rounded-xl overflow-hidden mt-4">

        {/* Column headers */}
        <div className="px-5 py-3 border-b border-border bg-ground/50">
          <div className="grid grid-cols-[3.5rem_minmax(0,1fr)_minmax(4rem,1fr)_3.5rem_3rem] gap-2 items-center">
            <span className="font-label text-[10px] font-semibold tracking-widest uppercase text-muted">
              Qualifying
            </span>
            <span className="font-label text-[10px] font-semibold tracking-widest uppercase text-muted">
              Driver
            </span>
            <span /> {/* connector spacer */}
            <span className="font-label text-[10px] font-semibold tracking-widest uppercase text-muted">
              Predicted
            </span>
            <span className="font-label text-[10px] font-semibold tracking-widest uppercase text-muted text-right">
              Δ
            </span>
          </div>
        </div>

        {/* Animated rows — isolation:isolate creates a stacking context so row z-indices
             can't escape and paint over the column headers above */}
        <div className="relative overflow-hidden" style={{ height: byPredicted.length * ROW_H, isolation: 'isolate' }}>
          {byPredicted.map((row, predIndex) => {
            const gridIndex = gridIndexOf.get(row.driver) ?? predIndex
            const openingOffset = (gridIndex - predIndex) * ROW_H
            const delta = row.grid_pos - row.rank
            const gaining = delta > 0
            const losing = delta < 0
            // Stagger by qualifying index so P1 qualifier starts first, not P1 predicted
            const delay = Math.min(gridIndex * STAGGER_MS, STAGGER_CAP)

            const lineColor = gaining ? COLOR_GAIN : losing ? COLOR_LOSS : COLOR_NEUTRAL
            const predColor = gaining ? COLOR_GAIN : losing ? COLOR_LOSS : undefined

            return (
              <div
                key={row.driver}
                className={`absolute inset-x-0 grid grid-cols-[3.5rem_minmax(0,1fr)_minmax(4rem,1fr)_3.5rem_3rem]
                           gap-2 items-center px-5 transition-colors hover:bg-ground/60${
                             predIndex < byPredicted.length - 1 ? ' border-b border-border' : ''
                           }`}
                style={{
                  top: predIndex * ROW_H,
                  height: ROW_H,
                  transform: settled ? 'translateY(0)' : `translateY(${openingOffset}px)`,
                  // 'none' when jumping to start so rows don't animate backwards on reset
                  transition: settled
                    ? `transform ${SLIDE_MS}ms cubic-bezier(0.16, 1, 0.3, 1), background-color 0.15s ease`
                    : 'none',
                  transitionDelay: settled ? `${delay}ms, 0ms` : '0ms',
                  willChange: 'transform',
                  // Bigger movers get higher z-index so they stay visible when crossing other rows
                  zIndex: settled ? 'auto' : 1 + Math.abs(delta),
                }}
              >
                {/* Qualifying position */}
                <span className="font-data text-sm text-muted">
                  P{row.grid_pos}
                </span>

                {/* Driver name */}
                <span className="font-label font-semibold text-sm text-ink truncate">
                  {driverDisplay(row.driver)}
                </span>

                {/* Connector line + arrow */}
                <div className="flex items-center gap-1 overflow-hidden">
                  <div
                    className="flex-1 h-px"
                    style={{ backgroundColor: lineColor, opacity: 0.5 }}
                  />
                  <span
                    className="font-data text-xs shrink-0"
                    style={{ color: lineColor }}
                  >
                    →
                  </span>
                </div>

                {/* Predicted position */}
                <span
                  className="font-data font-semibold text-sm"
                  style={{
                    color: predColor ?? '#111827',
                    opacity: settled ? 1 : 0,
                    transition: `opacity ${REVEAL_MS}ms ease`,
                    transitionDelay: `${delay + REVEAL_LAG}ms`,
                  }}
                >
                  P{row.rank}
                </span>

                {/* Delta */}
                <span
                  className="font-data font-semibold text-xs text-right"
                  style={{
                    opacity: settled ? 1 : 0,
                    transition: `opacity ${REVEAL_MS}ms ease`,
                    transitionDelay: `${delay + REVEAL_LAG}ms`,
                  }}
                >
                  {delta === 0 ? (
                    <span className="text-muted font-normal">—</span>
                  ) : (
                    <span style={{ color: lineColor }}>
                      {gaining ? '↑' : '↓'}{Math.abs(delta)}
                    </span>
                  )}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
