import type { PredictionRow } from '../../types'
import { useInView } from '../../hooks/useInView'
import TeamBadge from '../ui/TeamBadge'

interface PodiumProps {
  predictions: PredictionRow[]
  embedded?: boolean
}

const PODIUM_HEIGHTS = { 1: 'h-20', 2: 'h-14', 3: 'h-10' }
const PODIUM_DELAY = { 2: '0ms', 1: '150ms', 3: '300ms' }

interface PodiumSlotProps {
  row: PredictionRow
  position: 1 | 2 | 3
  inView: boolean
}

function PodiumSlot({ row, position, inView }: PodiumSlotProps) {
  const height = PODIUM_HEIGHTS[position]
  const delay = PODIUM_DELAY[position]

  const bgColor = position === 1 ? '#D4AF37' : position === 2 ? '#A8A9AD' : '#CD7F32'

  return (
    <div
      className={`flex flex-col items-center transition-all duration-700`}
      style={{
        opacity: inView ? 1 : 0,
        transform: inView ? 'translateY(0)' : 'translateY(24px)',
        transitionDelay: delay,
      }}
    >
      {/* Driver info above podium */}
      <div className="text-center mb-2">
        <p className="font-display font-bold text-base text-ink tracking-tight leading-tight">
          {row.driver.toUpperCase()}
        </p>
        <div className="flex items-center justify-center gap-1 mt-0.5">
          <TeamBadge team={row.team} className="w-4 h-4 rounded-sm" />
          <p className="font-label text-xs text-muted">{row.team}</p>
        </div>
      </div>

      {/* Podium block */}
      <div
        className={`w-24 sm:w-28 ${height} rounded-t-lg flex items-center justify-center`}
        style={{ backgroundColor: bgColor }}
        aria-label={`Position ${position}`}
      >
        <span className="font-display font-black text-2xl text-white/90">
          {position}
        </span>
      </div>
    </div>
  )
}

export default function Podium({ predictions, embedded = false }: PodiumProps) {
  const [ref, inView] = useInView<HTMLDivElement>({ threshold: 0.2 })

  const p1 = predictions.find(p => p.rank === 1)
  const p2 = predictions.find(p => p.rank === 2)
  const p3 = predictions.find(p => p.rank === 3)

  if (!p1) return null

  const heading = (
    <div className={embedded ? 'mb-6' : 'mb-8'}>
      <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
        Prediction
      </p>
      <h2 className="font-display font-bold text-xl text-ink tracking-tight">
        PREDICTED PODIUM
      </h2>
    </div>
  )

  const podium = (
    <div className="flex items-end justify-center gap-3 sm:gap-6">
      {p2 && <PodiumSlot row={p2} position={2} inView={inView} />}
      {p1 && <PodiumSlot row={p1} position={1} inView={inView} />}
      {p3 && <PodiumSlot row={p3} position={3} inView={inView} />}
    </div>
  )

  if (embedded) {
    return (
      <div ref={ref} className="bg-surface border border-border rounded-2xl p-6">
        {heading}
        {podium}
      </div>
    )
  }

  return (
    <section ref={ref} className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
      {heading}
      {podium}
    </section>
  )
}
