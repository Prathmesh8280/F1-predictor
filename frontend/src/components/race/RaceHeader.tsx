import type { RaceEntry } from '../../types'
import { CIRCUIT_META, ROUND_MAP_2026 } from '../../constants/races'
import { driverDisplay } from '../../constants/drivers'
import RaceSelect from './RaceSelect'

const SEASON_ROUNDS = Object.keys(ROUND_MAP_2026).length

interface RaceHeaderProps {
  races: RaceEntry[]
  selectedRace: string
  year: number
  onRaceChange: (race: string) => void
  loading: boolean
  isPreQualifying: boolean
}

function fmtFullDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function RaceHeader({
  races,
  selectedRace,
  year,
  onRaceChange,
  loading,
  isPreQualifying,
}: RaceHeaderProps) {
  const selected = races.find(r => r.name === selectedRace)
  const status = selected?.status
  const meta = selected ? CIRCUIT_META[selected.name] : undefined

  const statusLabel =
    status === 'completed'
      ? 'RACE COMPLETED'
      : isPreQualifying
      ? 'PRE-QUALIFYING'
      : 'QUALIFYING COMPLETE'
  const statusTone: 'completed' | 'accent' | 'muted' =
    status === 'completed' ? 'completed' : isPreQualifying ? 'muted' : 'accent'

  return (
    <section className="bg-surface border-b border-border">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5">
        <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-1.5">
          {year} Season
        </p>
        <RaceSelect
          races={races}
          selectedRace={selectedRace}
          onRaceChange={onRaceChange}
          disabled={loading}
          statusLabel={selected ? statusLabel : undefined}
          statusTone={statusTone}
        />

        {/* Context sub-line for the selected race */}
        {selected && (
          <div className="flex items-center gap-x-3 gap-y-1 flex-wrap mt-3 font-data text-sm text-muted">
            <span>
              Round <span className="text-ink font-semibold">{selected.round}</span>
              {SEASON_ROUNDS > 0 && <span> of {SEASON_ROUNDS}</span>}
            </span>
            {meta?.name && (
              <>
                <span className="w-1 h-1 rounded-full bg-border" />
                <span className="text-ink font-semibold">{meta.name}</span>
              </>
            )}
            <span className="w-1 h-1 rounded-full bg-border" />
            <span className="text-ink font-semibold">{fmtFullDate(selected.date)}</span>
            {selected.status === 'completed' && selected.winner && (
              <>
                <span className="w-1 h-1 rounded-full bg-border" />
                <span>
                  Winner{' '}
                  <span className="text-ink font-semibold">
                    {driverDisplay(selected.winner)}
                  </span>
                </span>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
