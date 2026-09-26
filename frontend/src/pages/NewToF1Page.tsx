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

function TermCard({ term, desc }: { term: string; desc: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <p className="font-label font-semibold text-sm text-ink mb-1">{term}</p>
      <p className="font-body text-xs text-muted leading-relaxed">{desc}</p>
    </div>
  )
}

function Callout({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-ground border border-border rounded-lg p-4">
      <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-ink mb-1">{title}</p>
      <p className="font-body text-xs text-muted leading-relaxed">{children}</p>
    </div>
  )
}

function StageBox({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <div className="text-center min-w-0">
      <p className="font-label text-[9px] sm:text-[10px] tracking-widest uppercase text-muted mb-1">{label}</p>
      <p className={`font-data font-bold text-xl sm:text-2xl leading-none ${accent ? 'text-accent' : 'text-ink'}`}>
        {value}
      </p>
      {sub && <p className="font-data text-[10px] text-positive mt-1">{sub}</p>}
    </div>
  )
}

export default function NewToF1Page() {
  return (
    <div className="min-h-screen bg-bg">
      {/* Hero */}
      <div className="bg-topbar text-white py-14">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-3">
            Getting Started
          </p>
          <h1 className="font-display font-black text-3xl sm:text-5xl tracking-tight mb-6">
            NEW TO F1?
          </h1>
          <p className="font-body text-fluid-lead text-white/60 max-w-xl">
            A two-minute guide to the F1 basics you need to understand this site. No prior knowledge required.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <Section number="01" title="THE RACE WEEKEND">
          <p className="font-body text-sm text-muted leading-relaxed mb-3">
            A Formula 1 event runs over a weekend and ends with the race on Sunday. Two parts matter for everything on this site:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TermCard
              term="Qualifying"
              desc="Qualifying is a timed session that determines the starting order, known as the grid. The fastest driver takes the first grid position, called pole position."
            />
            <TermCard
              term="The Race"
              desc="Drivers start from their grid positions and race the Grand Prix. Where they finish is their finishing position."
            />
          </div>
          <div className="mt-1">
            <Callout title="Some weekends have a Sprint">
              A Sprint weekend includes a shorter Saturday race in addition to the main Grand Prix. The Sprint has its own qualifying session and awards championship points. Six of the 2026 season's race weekends are Sprint weekends.
            </Callout>
          </div>
        </Section>

        <Section number="02" title="READING POSITIONS">
          <p className="font-body text-sm text-muted leading-relaxed mb-3">
            Positions are written as <strong>P1, P2, P3…</strong> A lower number means a better position. P1 means first place. In a completed race, P1 is the winner; on the starting grid, P1 means pole position.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TermCard term="Pole position" desc="P1 on the grid — the best possible start, earned by the fastest lap in qualifying." />
            <TermCard
              term="Grid vs finish"
              desc="Grid is where a driver starts the race. Qualifying normally determines the grid, although penalties can sometimes change a driver's starting position."
            />
            <TermCard
              term="Gaining / losing places"
              desc="These describe the change between where a driver starts and where they finish. Start P8, finish P3 = gained 5 places."
            />
            <TermCard term="Podium" desc="The top three finishers — P1, P2 and P3." />
            <TermCard
              term="DNF"
              desc="DNF means 'Did Not Finish' — a driver who does not complete the race. This can happen because of a crash, mechanical problem, or another retirement."
            />
            <TermCard term="Driver codes" desc="Drivers are shown as three letters: VER = Verstappen, RUS = Russell, LEC = Leclerc, NOR = Norris." />
          </div>
        </Section>

        <Section number="03" title="DRIVERS, TEAMS & POINTS">
          <p className="font-body text-sm text-muted leading-relaxed mb-3">
            F1 teams run two cars, with each car driven by one driver. Teams are also called <strong>constructors</strong>.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TermCard
              term="Drivers' Championship"
              desc="The Drivers' Championship is the season-long competition between drivers. Drivers earn championship points from their results, and the driver with the most points leads the championship."
            />
            <TermCard
              term="Constructors' Championship"
              desc="The Constructors' Championship is the season-long competition between teams. The results of both drivers contribute to the team's total."
            />
            <TermCard
              term="How points work"
              desc="In a Grand Prix, the top 10 finishers score points: 25 for first, then 18, 15, 12, 10, 8, 6, 4, 2 and 1. On Sprint weekends, the top eight in the Sprint also score, from 8 for first down to 1 for eighth."
            />
            <TermCard
              term="Why form matters"
              desc="Recent and season-long performance can provide useful context for the next race. Our model uses form as one signal alongside qualifying and weekend pace."
            />
          </div>
        </Section>

        <Section number="04" title="READING OUR PREDICTIONS">
          <p className="font-body text-sm text-muted leading-relaxed mb-4">
            This site predicts the finishing order before the race starts, using the qualifying grid, season form, weekend pace, and other model signals.
          </p>

          {/* Worked example */}
          <div className="bg-ground border border-border rounded-xl p-5 mb-4">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-accent mb-4">
              How to read a prediction
            </p>
            <div className="flex items-start justify-center gap-4 sm:gap-8 mb-4">
              <StageBox label="Starts" value="P16" />
              <span className="font-data text-muted text-lg leading-none mt-4">→</span>
              <StageBox label="Predicted" value="P10" sub="↑ 6 places" accent />
              <span className="font-data text-muted text-lg leading-none mt-4">→</span>
              <StageBox label="Actual" value="P8" />
            </div>
            <p className="font-body text-sm text-muted leading-relaxed">
              The driver starts 16th on the grid, our model predicts 10th, and the driver actually finishes 8th. So the model predicted a six-place recovery, but its final prediction was two places away from the actual result.
            </p>
            <p className="font-label text-[10px] tracking-widest uppercase text-muted mt-3">
              Example values — not a live race
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TermCard term="Predicted finish" desc="Where our model expects a driver to finish — its predicted final position." />
            <TermCard
              term="Predicted vs grid"
              desc="We compare where a driver starts with where our model expects them to finish, showing who the model expects to gain or lose places."
            />
            <TermCard
              term="After the race"
              desc="Once the results are in, we compare our prediction with the actual finishing order and show how close the model was."
            />
            <TermCard
              term="Off by / difference"
              desc="How many positions separate our prediction from the driver's actual finish. A ✓ means the prediction exactly matched the finishing position."
            />
          </div>

          {/* Race lifecycle */}
          <div className="mt-6">
            <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-3">
              How this site works
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <TermCard term="Before qualifying" desc="The starting order is not confirmed yet, so the race prediction is not available." />
              <TermCard term="After qualifying" desc="The starting grid is known, allowing the model to generate the race prediction." />
              <TermCard term="After the race" desc="The actual results are available, so we compare them with the prediction." />
            </div>
          </div>

          <p className="font-body text-sm text-muted leading-relaxed mt-6">
            Want the technical detail on the model itself? See{' '}
            <a href="/how-it-works" className="text-accent hover:text-accent-dark underline underline-offset-2">
              The Model
            </a>
            .
          </p>
        </Section>
      </div>
    </div>
  )
}
