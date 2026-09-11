import type { PredictionResponse } from '../../types'
import { useInView } from '../../hooks/useInView'
import { useCountUp } from '../../hooks/useCountUp'

interface ModelPerformanceProps {
  data: PredictionResponse
}

function MetricBlock({ label, value, active }: { label: string; value: number | null; active: boolean }) {
  const displayed = useCountUp(value ?? 0, 700, active && value != null)

  if (value == null) {
    return (
      <div className="bg-surface border border-border rounded-xl p-5">
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-1">{label}</p>
        <p className="font-body text-sm text-muted">Metric unavailable</p>
      </div>
    )
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-5">
      <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-1">{label}</p>
      <p className="font-data font-bold text-3xl text-ink">
        {displayed.toFixed(2)}
      </p>
      <p className="font-label text-xs text-muted mt-1">Mean Absolute Error</p>
    </div>
  )
}

export default function ModelPerformance({ data }: ModelPerformanceProps) {
  const [ref, inView] = useInView<HTMLDivElement>({ threshold: 0.3 })
  const { model_mae, baseline_mae } = data

  const improvementPct =
    model_mae != null && baseline_mae != null && baseline_mae > 0
      ? ((baseline_mae - model_mae) / baseline_mae) * 100
      : null

  return (
    <section ref={ref} className="max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Performance
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          DOES THE MODEL ACTUALLY HELP?
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <MetricBlock label="Our Model" value={model_mae} active={inView} />
        <MetricBlock label="Qualifying Baseline" value={baseline_mae} active={inView} />

        {improvementPct != null && (
          <div
            className="bg-positive/5 border border-positive/20 rounded-xl p-5"
          >
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-positive mb-1">
              Improvement
            </p>
            <p className="font-data font-bold text-3xl text-positive">
              {improvementPct.toFixed(1)}%
            </p>
            <p className="font-label text-xs text-positive/70 mt-1">Lower error vs baseline</p>
          </div>
        )}
      </div>

      <div className="bg-ground border border-border rounded-xl p-5">
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-2">
          What is the qualifying baseline?
        </p>
        <p className="font-body text-sm text-muted leading-relaxed">
          Qualifying order is already a strong predictor of race finish — drivers who qualify well tend to finish well. The model is evaluated against this baseline to show whether it adds value beyond simply copying the grid.
        </p>
      </div>
    </section>
  )
}
