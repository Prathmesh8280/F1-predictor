import type { PredictionResponse } from '../../types'
import { movers, ordinal, type Mover } from '../../lib/predictionSignals'
import { driverDisplay } from '../../constants/drivers'

interface Props {
  data: PredictionResponse
}

function MoveColumn({ title, tone, items }: { title: string; tone: 'pos' | 'neg'; items: Mover[] }) {
  const color = tone === 'pos' ? 'text-positive' : 'text-negative'
  const arrow = tone === 'pos' ? '↑' : '↓'

  return (
    <div>
      <p className={`font-label font-semibold text-[10px] tracking-widest uppercase ${color} mb-3`}>
        {title}
      </p>
      <div className="space-y-4">
        {items.map(({ row, delta }) => {
          const n = Math.abs(delta)
          return (
            <div key={row.driver} className="min-w-0">
              <p className="font-label font-semibold text-sm text-ink uppercase truncate leading-tight">
                {driverDisplay(row.driver)}
              </p>
              <p className="font-data text-xs text-muted mt-0.5">
                {ordinal(row.grid_pos)} → {ordinal(row.rank)}
              </p>
              <p className={`font-data font-bold text-sm mt-0.5 ${color}`}>
                {arrow} {n} position{n === 1 ? '' : 's'}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function PredictionContextPanel({ data }: Props) {
  const { gainers, losers } = movers(data.predictions, 3)

  return (
    <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col gap-6">
      <div>
        <span className="inline-block font-label font-semibold text-[9px] tracking-widest uppercase text-accent bg-accent/8 px-2.5 py-1 rounded-full mb-3">
          Pre-Race
        </span>
        <h2 className="font-display font-black text-2xl text-ink tracking-tight uppercase leading-tight">
          Biggest Expected Moves
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:gap-6">
        <MoveColumn title="Gaining" tone="pos" items={gainers} />
        <MoveColumn title="Losing" tone="neg" items={losers} />
      </div>
    </div>
  )
}
