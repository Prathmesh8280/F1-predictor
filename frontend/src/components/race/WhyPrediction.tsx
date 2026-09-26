import type { PredictionRow } from '../../types'
import { signalSummary, winnerReasons } from '../../lib/predictionSignals'
import { driverDisplay } from '../../constants/drivers'

interface WhyPredictionProps {
  predictions: PredictionRow[]
}

export default function WhyPrediction({ predictions }: WhyPredictionProps) {
  const winner = [...predictions].sort((a, b) => a.rank - b.rank)[0]
  if (!winner) return null

  const reasons = winnerReasons(winner)
  const signals = signalSummary(winner)

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-8 border-t border-border">
      <div className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Model Reasoning
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          WHY THE MODEL THINKS THIS
        </h2>
        <p className="font-body text-sm text-muted mt-1">
          The model's prediction for {driverDisplay(winner.driver)} rests on a few key factors.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Numbered reasons */}
        <ol className="space-y-5">
          {reasons.map((r, i) => (
            <li key={r.title} className="flex gap-4">
              <span className="font-data font-black text-lg text-accent/30 leading-none shrink-0 w-8">
                {String(i + 1).padStart(2, '0')}
              </span>
              <div>
                <p className="font-label font-bold text-xs tracking-widest uppercase text-ink mb-1">
                  {r.title}
                </p>
                <p className="font-body text-sm text-muted leading-relaxed">{r.body}</p>
              </div>
            </li>
          ))}
        </ol>

        {/* Supporting model signals */}
        <div>
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-3">
            Model Signals
          </p>
          <dl className="space-y-2">
            {signals.map(({ label, value }) => (
              <div key={label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <dt className="font-label font-semibold text-sm text-muted">{label}</dt>
                <dd className="font-data font-semibold text-sm text-ink">{value}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-5">
            <a
              href="/how-it-works"
              className="inline-flex items-center gap-1.5 font-label font-semibold text-xs tracking-widest uppercase text-accent hover:text-accent-dark transition-colors focus-visible:outline-accent border border-accent/30 hover:border-accent px-4 py-2 rounded-lg"
            >
              See model details →
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
