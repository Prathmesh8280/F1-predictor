import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function ModelDetails() {
  const [expanded, setExpanded] = useState(false)

  return (
    <section id="model-details" className="scroll-mt-20 max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div className="mb-6">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Methodology
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          MODEL DETAILS
        </h2>
      </div>

      {/* Always-visible summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="bg-surface border border-border rounded-xl p-5">
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-accent mb-2">Stage 1</p>
          <h3 className="font-label font-bold text-base text-ink mb-2">Circuit-Specific Grid Effects</h3>
          <p className="font-body text-sm text-muted leading-relaxed">
            Learns how starting position historically translates to finishing position at each specific circuit. Some circuits allow more overtaking than others.
          </p>
        </div>

        <div className="bg-surface border border-border rounded-xl p-5">
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-accent mb-2">Stage 2</p>
          <h3 className="font-label font-bold text-base text-ink mb-2">Current Season Form</h3>
          <p className="font-body text-sm text-muted leading-relaxed">
            Incorporates championship standings, constructor rank, and weekend pace (FP2) to adjust the Stage 1 baseline with real current-season information.
          </p>
        </div>
      </div>

      {/* Expandable technical details */}
      <button
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-2 font-label font-semibold text-sm tracking-widest uppercase text-muted hover:text-ink transition-colors focus-visible:outline-accent"
        aria-expanded={expanded}
        aria-controls="model-technical-details"
      >
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {expanded ? 'Hide' : 'View'} technical details
      </button>

      {expanded && (
        <div id="model-technical-details" className="mt-5 space-y-5">
          <div className="bg-surface border border-border rounded-xl p-5">
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-ink mb-3">Algorithm</h3>
            <p className="font-body text-sm text-ink mb-2">
              <strong>Ridge Regression</strong> — a regularized linear model that handles correlated features well and generalizes from limited training data.
            </p>
            <p className="font-body text-sm text-muted">
              Both stages use Ridge regression. Regularization is applied to prevent overfitting on the small per-circuit training sets.
            </p>
          </div>

          <div className="bg-surface border border-border rounded-xl p-5">
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-ink mb-3">Features</h3>
            <ul className="space-y-2">
              {[
                'Qualifying (grid) position',
                'Championship standings rank',
                'Constructor standings rank',
                'FP2 pace rank (weekend pace proxy)',
                'Circuit-specific grid-to-finish delta (Stage 1)',
              ].map(f => (
                <li key={f} className="flex items-center gap-2 font-body text-sm text-ink">
                  <span className="w-1 h-1 bg-muted rounded-full flex-shrink-0" aria-hidden="true" />
                  {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-surface border border-border rounded-xl p-5">
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-ink mb-3">Evaluation</h3>
            <p className="font-body text-sm text-ink mb-2">
              <strong>Walk-forward backtesting</strong> across 36 races: for each race, the model is trained only on prior races, then tested on that race.
            </p>
            <p className="font-body text-sm text-muted">
              This prevents data leakage — the model never "sees" future information during evaluation.
            </p>
          </div>

          <div className="bg-ground border border-border rounded-xl p-5">
            <h3 className="font-label font-bold text-sm tracking-widest uppercase text-ink mb-2">Limitations</h3>
            <p className="font-body text-sm text-muted leading-relaxed">
              Race outcomes also depend on incidents, safety cars, pit strategy, mechanical reliability, and weather — factors that cannot be fully determined from pre-race information. This model predicts the most likely outcome based on available signals, not guaranteed results.
            </p>
          </div>
        </div>
      )}
    </section>
  )
}
