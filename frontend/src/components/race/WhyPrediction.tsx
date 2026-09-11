import type { PredictionRow } from '../../types'
import { signalSummary, predictionSentence } from '../../lib/predictionSignals'

interface WhyPredictionProps {
  predictions: PredictionRow[]
}

export default function WhyPrediction({ predictions }: WhyPredictionProps) {
  const winner = predictions.find(p => p.rank === 1)
  if (!winner) return null

  const sentence = predictionSentence(winner)
  const signals = signalSummary(winner)

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Model Reasoning
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          WHY THE MODEL THINKS THIS
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Explanation */}
        <div>
          <p className="font-body text-fluid-lead text-ink leading-relaxed mb-2">
            {sentence}
          </p>
          <p className="font-body text-sm text-muted">
            The model weighs qualifying position alongside current season form, constructor strength, weekend pace, and circuit-specific historical effects.
          </p>
        </div>

        {/* Signal grid */}
        <div>
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-3">
            Signals for {winner.driver.toUpperCase()}
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
