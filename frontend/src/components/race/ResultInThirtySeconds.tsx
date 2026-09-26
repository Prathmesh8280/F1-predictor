import type { PredictionResponse } from '../../types'
import { biggestMiss, podiumHitCount, resultVerdict } from '../../lib/predictionBriefing'
import { ordinal } from '../../lib/predictionSignals'
import { driverDisplay } from '../../constants/drivers'

interface Props {
  data: PredictionResponse
}

function Tile({ label, name, sub, tone }: { label: string; name: string; sub: string; tone?: 'accent' | 'positive' | 'negative' }) {
  const subColor =
    tone === 'accent' ? 'text-accent font-semibold' :
    tone === 'positive' ? 'text-positive font-semibold' :
    tone === 'negative' ? 'text-negative font-semibold' :
    'text-muted'
  return (
    <div className="min-w-0">
      <p className="font-label font-semibold text-[9px] sm:text-[10px] tracking-widest uppercase text-muted mb-1.5 leading-tight">
        {label}
      </p>
      <p className="font-display font-bold text-base sm:text-lg text-ink uppercase tracking-tight leading-none truncate">
        {name}
      </p>
      <p className={`font-data text-xs sm:text-sm mt-1 ${subColor}`}>{sub}</p>
    </div>
  )
}

export default function ResultInThirtySeconds({ data }: Props) {
  const { predictions } = data
  const completed = predictions.filter(p => p.actual_rank != null)
  if (completed.length === 0) return null

  const actualWinner = completed.find(p => p.actual_rank === 1)
  const hits = podiumHitCount(predictions)
  const swing = biggestMiss(predictions)
  const takeaway = resultVerdict(predictions)

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-6">
      <div className="bg-surface border border-border rounded-2xl p-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-4">
          Result in 30 Seconds
        </p>

        <div className="grid grid-cols-3 gap-3 sm:gap-6">
          <Tile label="Winner" name={actualWinner ? driverDisplay(actualWinner.driver) : '—'} sub="1st" />
          <Tile
            label="Podium Hit"
            name={`${hits} / 3`}
            sub="podium spots correct"
            tone={hits > 0 ? 'positive' : undefined}
          />
          <Tile
            label="Biggest Prediction Swing"
            name={swing ? driverDisplay(swing.row.driver) : '—'}
            sub={swing ? `Predicted ${ordinal(swing.row.rank)} → Finished ${ordinal(swing.row.actual_rank as number)}` : ''}
            tone="accent"
          />
        </div>

        {takeaway && (
          <div className="mt-5 pt-4 border-t border-border">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-1">
              Takeaway
            </p>
            <p className="font-body text-sm text-ink leading-relaxed">
              {takeaway}{' '}
              <a
                href="/new-to-f1"
                className="text-accent/70 hover:text-accent underline underline-offset-2"
              >
                New to these terms? Read the F1 basics →
              </a>
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
