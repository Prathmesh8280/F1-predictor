import type { PredictionResponse } from '../../types'
import { biggestGainer, keyStoryLine } from '../../lib/predictionBriefing'
import { ordinal } from '../../lib/predictionSignals'
import { driverDisplay } from '../../constants/drivers'

interface Props {
  data: PredictionResponse
}

function Tile({ label, name, sub, accent }: { label: string; name: string; sub: string; accent?: boolean }) {
  return (
    <div className="min-w-0">
      <p className="font-label font-semibold text-[9px] sm:text-[10px] tracking-widest uppercase text-muted mb-1.5 leading-tight">
        {label}
      </p>
      <p className="font-display font-bold text-base sm:text-lg text-ink uppercase tracking-tight leading-none truncate">
        {name}
      </p>
      <p className={`font-data text-xs sm:text-sm mt-1 ${accent ? 'text-accent font-semibold' : 'text-muted'}`}>
        {sub}
      </p>
    </div>
  )
}

export default function RaceInThirtySeconds({ data }: Props) {
  const { predictions } = data
  const winner = [...predictions].sort((a, b) => a.rank - b.rank)[0]
  if (!winner) return null

  const pole = predictions.find(p => p.grid_pos === 1)
  const move = biggestGainer(predictions)
  const story = keyStoryLine(predictions)

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-6">
      <div className="bg-surface border border-border rounded-2xl p-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-4">
          Race in 30 Seconds
        </p>

        <div className="grid grid-cols-3 gap-3 sm:gap-6">
          <Tile label="Pole" name={pole ? driverDisplay(pole.driver) : '—'} sub={pole ? '1st' : ''} />
          <Tile label="Model's Winner" name={driverDisplay(winner.driver)} sub={ordinal(winner.rank)} />
          <Tile
            label="Biggest Move"
            name={move ? driverDisplay(move.row.driver) : '—'}
            sub={move ? `${ordinal(move.row.grid_pos)} → ${ordinal(move.row.rank)}` : ''}
            accent
          />
        </div>

        {story && (
          <div className="mt-5 pt-4 border-t border-border">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-1">
              Key Story
            </p>
            <p className="font-body text-sm text-ink leading-relaxed">{story}</p>
          </div>
        )}
      </div>
    </section>
  )
}
