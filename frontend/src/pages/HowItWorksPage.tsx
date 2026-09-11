interface SectionProps {
  number: string
  title: string
  children: React.ReactNode
}

function Section({ number, title, children }: SectionProps) {
  return (
    <div className="py-10 border-b border-border last:border-0">
      <div className="flex items-baseline gap-4 mb-4">
        <span className="font-display font-black text-2xl text-accent/25 flex-shrink-0">{number}</span>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">{title}</h2>
      </div>
      <div className="ml-12 space-y-3">{children}</div>
    </div>
  )
}

export default function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-bg">
      {/* Hero */}
      <div className="bg-topbar text-white py-14">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-3">
            Methodology
          </p>
          <h1 className="font-display font-black text-3xl sm:text-5xl tracking-tight mb-6">
            HOW IT WORKS
          </h1>
          <p className="font-body text-fluid-lead text-white/60 max-w-xl">
            Once qualifying sets the grid, a two-stage machine learning model takes over — combining circuit history, driver form, team performance, and weekend pace to predict how the race will unfold. No live data, no guesswork mid-race. Everything is decided before lights-out.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <Section number="01" title="THE PROBLEM">
          <p className="font-body text-sm text-muted leading-relaxed">
            Predicting an F1 race finishing order is genuinely difficult. Qualifying determines starting position, but the race itself involves 20 drivers, 50+ laps, varying tire strategies, weather, and random events. The question this project tries to answer is: <em>how well can the available pre-race information explain the final order?</em>
          </p>
        </Section>

        <Section number="02" title="THE DATA">
          <p className="font-body text-sm text-muted leading-relaxed mb-3">
            All data is sourced from <strong>FastF1</strong>, an open-source Python library for accessing F1 timing and telemetry data.
          </p>
          <ul className="space-y-2">
            {[
              'Qualifying results (grid positions)',
              'Race results (actual finishing positions)',
              'Driver championship standings',
              'Constructor championship standings',
              'FP2 lap time data (weekend pace proxy)',
              'Historical race data across multiple seasons',
            ].map(item => (
              <li key={item} className="flex items-start gap-2 font-body text-sm text-muted">
                <span className="w-1.5 h-1.5 bg-accent rounded-full flex-shrink-0 mt-1.5" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </Section>

        <Section number="03" title="FEATURE ENGINEERING">
          <p className="font-body text-sm text-muted leading-relaxed mb-3">
            Raw data is transformed into meaningful signals for the model:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { name: 'Grid position', desc: 'The qualifying rank — the strongest single predictor of race finish.' },
              { name: 'Championship rank', desc: 'Driver standings entering the race weekend.' },
              { name: 'Constructor rank', desc: 'Team performance in the current season.' },
              { name: 'FP2 pace rank', desc: 'Relative lap time in Friday practice — a proxy for race-weekend pace.' },
              { name: 'Circuit delta (Stage 1)', desc: 'Circuit-specific historical grid→finish tendency, estimated per circuit.' },
            ].map(({ name, desc }) => (
              <div key={name} className="bg-surface border border-border rounded-lg p-4">
                <p className="font-label font-semibold text-sm text-ink mb-1">{name}</p>
                <p className="font-body text-xs text-muted">{desc}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section number="04" title="TWO-STAGE MODEL">
          <p className="font-body text-sm text-muted leading-relaxed mb-4">
            The model uses two sequential Ridge regression stages:
          </p>
          <div className="space-y-4">
            <div className="bg-surface border border-border rounded-xl p-5">
              <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-accent mb-2">Stage 1 — Circuit Baseline</p>
              <p className="font-body text-sm text-muted leading-relaxed">
                Uses historical race data at each circuit to learn the typical grid→finish effect. At Monza, overtaking is high, so grid position matters less; at Monaco, grid position is almost everything.
              </p>
            </div>
            <div className="bg-surface border border-border rounded-xl p-5">
              <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-accent mb-2">Stage 2 — Season Form Adjustment</p>
              <p className="font-body text-sm text-muted leading-relaxed">
                Adjusts the Stage 1 baseline using current-season information: championship standing, constructor form, and weekend pace. This is skipped when standings data isn't available (e.g. the season opener).
              </p>
            </div>
            <div className="bg-ground border border-border rounded-lg p-4">
              <p className="font-body text-xs text-muted">
                Both stages use <strong>Ridge regression</strong> — not neural networks, not XGBoost, not a "custom AI engine." Regularized linear regression is appropriate for this problem: small training sets, correlated features, and a need for interpretability.
              </p>
            </div>
          </div>
        </Section>

        <Section number="05" title="THE FULL PIPELINE">
          <p className="font-body text-sm text-muted leading-relaxed mb-4">
            From raw F1 data to the prediction you see on screen:
          </p>
          <div className="bg-surface border border-border rounded-2xl p-5 max-w-sm">
            <div className="space-y-0">
              {[
                { label: 'F1 DATA', sub: 'FastF1 · Historical + current season results' },
                { label: 'FEATURE ENGINEERING', sub: 'Grid position, standings, FP2 pace, circuit effects' },
                { label: 'STAGE 1 — CIRCUIT BASELINE', sub: 'Ridge regression trained on historical circuit data' },
                { label: 'STAGE 2 — SEASON FORM', sub: 'Adjusts baseline with current-season driver & team form' },
                { label: 'FASTAPI BACKEND', sub: 'Serves predictions + race schedule via REST endpoints' },
                { label: 'REACT FRONTEND', sub: 'Displays predicted order, circuit context, post-race review' },
              ].map(({ label, sub }, i, arr) => (
                <div key={label}>
                  <div className="bg-ground border border-border rounded-lg px-4 py-3">
                    <p className="font-label font-bold text-sm text-ink tracking-wide">{label}</p>
                    <p className="font-body text-xs text-muted mt-0.5">{sub}</p>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="flex justify-center py-1.5">
                      <span className="font-data text-accent text-base leading-none">↓</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </Section>

        <Section number="06" title="EVALUATION">
          <p className="font-body text-sm text-muted leading-relaxed mb-4">
            The model is evaluated using <strong>walk-forward backtesting</strong> across 36 historical races:
          </p>
          <div className="bg-surface border border-border rounded-xl p-5 mb-4">
            <div className="flex items-center gap-4 font-data text-sm">
              <div className="text-center">
                <p className="text-muted text-xs mb-1">Train</p>
                <p className="font-semibold text-ink">Races 1…N-1</p>
              </div>
              <span className="text-accent">→</span>
              <div className="text-center">
                <p className="text-muted text-xs mb-1">Test</p>
                <p className="font-semibold text-ink">Race N</p>
              </div>
              <span className="text-accent">→</span>
              <div className="text-center">
                <p className="text-muted text-xs mb-1">Score</p>
                <p className="font-semibold text-ink">MAE</p>
              </div>
            </div>
          </div>
          <p className="font-body text-sm text-muted leading-relaxed mb-4">
            This prevents data leakage — the model never sees future information during evaluation.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="font-label text-[10px] tracking-widest uppercase text-muted mb-1">Our model MAE</p>
              <p className="font-data font-bold text-2xl text-ink">2.08</p>
            </div>
            <div className="bg-surface border border-border rounded-lg p-4">
              <p className="font-label text-[10px] tracking-widest uppercase text-muted mb-1">Qualifying baseline MAE</p>
              <p className="font-data font-bold text-2xl text-muted">2.19</p>
            </div>
          </div>
          <p className="font-body text-xs text-muted mt-3">
            Qualifying order is already a strong predictor of race finish. The model improves on that baseline by ~5%.
          </p>
        </Section>

        <Section number="07" title="LIMITATIONS">
          <div className="bg-ground border border-border rounded-xl p-5">
            <p className="font-body text-sm text-muted leading-relaxed">
              Race outcomes also depend on incidents, safety cars, pit strategy, mechanical reliability, and weather — factors that cannot be fully determined from pre-race information. A driver could qualify P2 and win due to a Safety Car, or qualify P1 and retire with a mechanical failure. This model predicts the most statistically likely outcome given the available signals — not guaranteed results.
            </p>
          </div>
          <div className="mt-4 space-y-2">
            {[
              'No live telemetry data — all inputs are pre-race',
              'Safety car events are not predictable from pre-race data',
              'Pit strategy decisions happen during the race',
              'Weather changes are not modeled',
              'First-lap incidents are not predictable',
            ].map(item => (
              <div key={item} className="flex items-start gap-2 font-body text-xs text-muted">
                <span className="text-warning mt-0.5">⚠</span>
                {item}
              </div>
            ))}
          </div>
        </Section>
      </div>
    </div>
  )
}
