import type { PredictionResponse, PredictionRow } from '../../types'
import TeamBadge from '../ui/TeamBadge'

interface PredictionHeroProps {
  data: PredictionResponse
}

function podiumRow(predictions: PredictionRow[], rank: number): PredictionRow | undefined {
  return predictions.find(p => p.rank === rank)
}

export default function PredictionHero({ data }: PredictionHeroProps) {
  const { predictions, race, year, circuit, is_completed } = data
  const winner = podiumRow(predictions, 1)
  const p2 = podiumRow(predictions, 2)
  const p3 = podiumRow(predictions, 3)

  if (!winner) return null

  return (
    <section className="bg-topbar text-white overflow-hidden">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        {/* Race identity + status */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-8">
          <div>
            <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-white/50 mb-1">
              {circuit.name}
            </p>
            <h1 className="font-display font-black text-2xl sm:text-3xl tracking-tight">
              {race.toUpperCase()} GRAND PRIX · {year}
            </h1>
          </div>
          <span
            className={`self-start font-label font-semibold text-[10px] tracking-widest uppercase px-2.5 py-1.5 rounded-full mt-1 ${
              is_completed
                ? 'bg-white/10 text-white/70'
                : 'bg-accent/20 text-accent border border-accent/30'
            }`}
          >
            {is_completed ? 'RACE COMPLETED' : 'PRE-RACE PREDICTION'}
          </span>
        </div>

        {/* OUR PREDICTION label */}
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-4">
          {is_completed ? 'Our Pre-Race Prediction' : 'Our Prediction'}
        </p>

        {/* P1 winner — dominant */}
        <div className="mb-8">
          <div
            className="inline-block text-[4.5rem] sm:text-[6rem] font-display font-black leading-none tracking-tighter"
            style={{ color: 'rgba(255,255,255,0.12)' }}
          >
            P1
          </div>
          <div className="-mt-4 sm:-mt-6">
            <h2
              className="font-display font-black text-fluid-hero leading-none tracking-tighter"
              style={{ color: '#FFFFFF' }}
            >
              {winner.driver.toUpperCase()}
            </h2>
            <div className="flex items-center gap-1.5 mt-2">
              <TeamBadge team={winner.team} className="w-4 h-4 rounded-sm" />
              <span className="font-label font-semibold text-sm text-white/60">
                {winner.team}
              </span>
            </div>
          </div>
        </div>

        {/* P2 / P3 secondary */}
        <div className="flex flex-wrap gap-6 sm:gap-10">
          {p2 && (
            <div>
              <span className="font-data font-semibold text-sm text-white/40 block mb-0.5">P2</span>
              <span className="font-display font-bold text-xl text-white tracking-tight">{p2.driver.toUpperCase()}</span>
              <div className="flex items-center gap-1 mt-1">
                <TeamBadge team={p2.team} className="w-3.5 h-3.5 rounded-sm" />
                <span className="font-label text-xs text-white/50">{p2.team}</span>
              </div>
            </div>
          )}
          {p3 && (
            <div>
              <span className="font-data font-semibold text-sm text-white/40 block mb-0.5">P3</span>
              <span className="font-display font-bold text-xl text-white tracking-tight">{p3.driver.toUpperCase()}</span>
              <div className="flex items-center gap-1 mt-1">
                <TeamBadge team={p3.team} className="w-3.5 h-3.5 rounded-sm" />
                <span className="font-label text-xs text-white/50">{p3.team}</span>
              </div>
            </div>
          )}
        </div>

        {/* Explore CTA */}
        <div className="mt-8">
          <a
            href="#full-order"
            className="inline-flex items-center gap-2 font-label font-semibold text-sm tracking-widest uppercase text-white/60 hover:text-white transition-colors focus-visible:outline-accent"
          >
            {is_completed ? 'See prediction details ↓' : 'Explore full prediction ↓'}
          </a>
        </div>
      </div>
    </section>
  )
}
