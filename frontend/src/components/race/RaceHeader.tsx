import type { RaceEntry } from '../../types'

interface RaceHeaderProps {
  races: RaceEntry[]
  selectedRace: string
  year: number
  onRaceChange: (race: string) => void
  onPredict: () => void
  loading: boolean
  hasPrediction: boolean
  isPreQualifying: boolean
}

export default function RaceHeader({
  races,
  selectedRace,
  year,
  onRaceChange,
  onPredict,
  loading,
  hasPrediction,
  isPreQualifying,
}: RaceHeaderProps) {
  const selected = races.find(r => r.name === selectedRace)
  const status = selected?.status

  const buttonLabel = loading ? 'Analyzing…' : hasPrediction ? 'REFRESH' : 'PREDICT'

  return (
    <section className="bg-surface border-b border-border">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {/* Season + Race selector */}
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted">
              {year} Season
            </p>
            <div className="flex items-center gap-3 flex-wrap">
              <select
                value={selectedRace}
                onChange={e => onRaceChange(e.target.value)}
                disabled={loading}
                aria-label="Select race"
                className="font-label font-semibold text-base text-ink bg-transparent border border-border rounded-lg px-3 py-2 pr-8 focus:border-accent focus:outline-none transition-colors cursor-pointer disabled:opacity-50 appearance-none"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236B6876' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                }}
              >
                {races.map(r => (
                  <option key={r.name} value={r.name}>
                    {r.name} Grand Prix
                  </option>
                ))}
              </select>

              {status && (
                <span
                  className={`font-label font-semibold text-[10px] tracking-widest uppercase px-2 py-1 rounded-full ${
                    status === 'completed'
                      ? 'bg-positive/10 text-positive'
                      : isPreQualifying
                      ? 'bg-muted/10 text-muted'
                      : 'bg-accent/10 text-accent'
                  }`}
                >
                  {status === 'completed'
                    ? 'RACE COMPLETED'
                    : isPreQualifying
                    ? 'PRE-QUALIFYING'
                    : 'QUALIFYING COMPLETE'}
                </span>
              )}
            </div>
          </div>

          {/* Only show the predict button when qualifying is done */}
          {!isPreQualifying && (
            <button
              onClick={onPredict}
              disabled={loading}
              aria-label={hasPrediction ? 'Refresh prediction' : 'Generate prediction'}
              className="font-label font-bold text-sm tracking-widest uppercase px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-accent whitespace-nowrap"
            >
              {buttonLabel}
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
