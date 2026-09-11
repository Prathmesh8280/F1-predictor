import type { PredictionResponse, PredictionRow } from '../../types'
import TeamBadge from '../ui/TeamBadge'
import { driverDisplay } from '../../constants/drivers'

interface Props {
  data: PredictionResponse
}

function PodiumSlot({ row, pos }: { row: PredictionRow | undefined; pos: number }) {
  if (!row) return <div className="flex-1" />

  const platformH = pos === 1 ? 'h-12' : pos === 2 ? 'h-8' : 'h-5'
  const platformBg = pos === 1 ? 'bg-accent/25' : 'bg-border/70'
  const isFirst = pos === 1

  return (
    <div className="flex flex-col items-center flex-1 min-w-0">
      <TeamBadge team={row.team} className={`${isFirst ? 'w-6 h-6' : 'w-5 h-5'} rounded-sm mb-1.5`} />
      <p className={`font-label font-bold text-ink uppercase text-center leading-tight mb-2 px-0.5 ${isFirst ? 'text-xs' : 'text-[9px]'}`}>
        {driverDisplay(row.driver)}
      </p>
      <div className={`w-full ${platformH} ${platformBg} rounded-t-sm flex items-center justify-center`}>
        <span className={`font-data font-bold text-muted ${isFirst ? 'text-sm' : 'text-xs'}`}>
          P{pos}
        </span>
      </div>
    </div>
  )
}

export default function PredictionSummaryPanel({ data }: Props) {
  const { race, year, circuit, predictions } = data
  const p1 = predictions.find(r => r.rank === 1)
  const p2 = predictions.find(r => r.rank === 2)
  const p3 = predictions.find(r => r.rank === 3)

  return (
    <div className="bg-surface border border-border rounded-2xl p-6 flex flex-col gap-6">

      {/* Race identity */}
      <div>
        <span className="inline-block font-label font-semibold text-[9px] tracking-widest uppercase text-accent bg-accent/10 px-2.5 py-1 rounded-full mb-3">
          Qualifying Complete
        </span>
        <h2 className="font-display font-black text-2xl text-ink tracking-tight uppercase leading-tight">
          {race} Grand Prix
        </h2>
        <p className="font-label font-semibold text-xs text-muted tracking-widest uppercase mt-1">
          {circuit.name} · {year}
        </p>
      </div>

      {/* Predicted podium */}
      <div>
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-accent mb-4">
          Our Pre-Race Prediction
        </p>
        <div className="flex items-end gap-1.5">
          <PodiumSlot row={p2} pos={2} />
          <PodiumSlot row={p1} pos={1} />
          <PodiumSlot row={p3} pos={3} />
        </div>
      </div>
    </div>
  )
}
