import { useEffect, useMemo, useState } from 'react'
import type { RaceEntry, AppState } from '../types'
import { fetchRaces, fetchPrediction, ApiError } from '../api/client'
import { CIRCUIT_META, OVERTAKING_CONFIG } from '../constants/races'

import RaceHeader from '../components/race/RaceHeader'
import PredictionSummaryPanel from '../components/race/PredictionSummaryPanel'
import PredictionContextPanel from '../components/race/PredictionContextPanel'
import WhyPrediction from '../components/race/WhyPrediction'
import PredictionTable from '../components/race/PredictionTable'
import CircuitContext from '../components/race/CircuitContext'
import RaceStory from '../components/race/RaceStory'
import RaceSummaryPanel from '../components/race/RaceSummaryPanel'
import PerformancePanel from '../components/race/PerformancePanel'
import ActualVsPredicted from '../components/race/ActualVsPredicted'
import LastRaceCard from '../components/race/LastRaceCard'
import type { LastRaceStatus } from '../components/race/LastRaceCard'
import LoadingState from '../components/ui/LoadingState'
import ErrorState from '../components/ui/ErrorState'

const YEAR = 2026

/**
 * Returns true if today is more than 1 day before the race Sunday —
 * meaning qualifying (Saturday) has not happened yet.
 */
function isBeforeQualifying(race: RaceEntry): boolean {
  if (race.status === 'completed') return false
  const [y, m, d] = race.date.split('-').map(Number)
  const raceDay = new Date(y, m - 1, d)
  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)
  const daysUntil = Math.round(
    (raceDay.getTime() - todayStart.getTime()) / (24 * 60 * 60 * 1000),
  )
  return daysUntil > 1
}

function stateForRace(race: RaceEntry, raceName: string): AppState {
  return isBeforeQualifying(race)
    ? { phase: 'pre-qualifying', race: raceName, year: YEAR }
    : { phase: 'idle' }
}

// ─── Pre-qualifying layout ────────────────────────────────────────────────────

interface PreQualifyingProps {
  race: string
  previousRace: RaceEntry | null
  lastRaceStatus: LastRaceStatus
  onViewPreviousRace: () => void
}

function PreQualifyingState({
  race,
  previousRace,
  lastRaceStatus,
  onViewPreviousRace,
}: PreQualifyingProps) {
  const [imgError, setImgError] = useState(false)
  const circuitMeta = CIRCUIT_META[race]
  const officialName = circuitMeta?.officialName ?? `${race} Grand Prix`
  const circuitName = circuitMeta?.name ?? null
  const overtakingCfg = circuitMeta?.overtaking ? OVERTAKING_CONFIG[circuitMeta.overtaking] : null

  const lifecycle = [
    { label: 'Qualifying', sub: 'Grid confirmed', active: true },
    { label: 'Prediction', sub: 'Model runs', active: false },
    { label: 'Race', sub: 'Prediction vs result', active: false },
  ]

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-14">

        {/* LEFT — Race identity + prediction availability */}
        <div>
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-3">
            Next Race
          </p>
          <h2 className="font-display font-bold text-fluid-hero text-ink leading-none mb-2 uppercase">
            {race}
          </h2>
          <div className="mb-8">
            <p className="font-label font-semibold text-sm text-ink mb-0.5">
              {officialName}
            </p>
            {circuitName && (
              <p className="font-label font-semibold text-xs text-muted tracking-widest uppercase">
                {circuitName} · {YEAR}
              </p>
            )}
          </div>

          <div className="bg-surface border border-border rounded-xl p-5 mb-8">
            <p className="font-label font-bold text-sm text-ink mb-1.5">
              Prediction available after qualifying
            </p>
            <p className="font-body text-sm text-muted leading-relaxed">
              Qualifying sets the starting point. Once the grid is confirmed, the
              model predicts how the race could unfold.
            </p>
          </div>

          {/* What Happens Next */}
          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-3">
            What Happens Next
          </p>
          <div className="flex flex-col mb-8">
            {lifecycle.map(({ label, sub, active }, i) => (
              <div key={label}>
                <div
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg ${
                    active ? 'bg-accent/5 border border-accent/20' : ''
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      active ? 'bg-accent' : 'bg-border'
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <span
                      className={`font-label font-bold text-xs tracking-widest uppercase ${
                        active ? 'text-accent' : 'text-muted'
                      }`}
                    >
                      {label}
                    </span>
                    <span className="font-body text-xs text-muted ml-2">{sub}</span>
                  </div>
                  {active && (
                    <span className="font-label font-semibold text-[9px] tracking-widest uppercase text-accent bg-accent/10 px-2 py-0.5 rounded-full shrink-0">
                      Next
                    </span>
                  )}
                </div>
                {i < lifecycle.length - 1 && (
                  <div className="pl-[18px] leading-none py-0.5 text-border text-xs select-none">
                    │
                  </div>
                )}
              </div>
            ))}
          </div>

          <p className="font-label font-semibold text-[10px] tracking-widest uppercase text-muted mb-4">
            What the model will use
          </p>
          <div className="flex flex-col gap-3">
            {['Qualifying grid', 'Circuit history', 'Season form', 'Weekend pace'].map(
              (item, i) => (
                <div key={item} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-surface border border-border flex items-center justify-center font-data text-xs text-muted shrink-0">
                    {i + 1}
                  </span>
                  <span className="font-body text-sm text-ink">{item}</span>
                </div>
              ),
            )}
            <div className="flex items-start gap-3 mt-1 pl-1">
              <span className="w-6 h-6 flex items-center justify-center text-accent font-bold text-base shrink-0 mt-0.5">
                ↓
              </span>
              <div>
                <span className="font-label font-bold text-sm text-accent tracking-widest uppercase">
                  Race Prediction
                </span>
                <p className="font-label text-[10px] tracking-widest uppercase text-muted mt-0.5">
                  Unlocks after qualifying
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT — Last Race card */}
        <div>
          <LastRaceCard
            previousRace={previousRace}
            status={lastRaceStatus}
            onViewFullReview={onViewPreviousRace}
          />
        </div>
      </div>

      {/* Circuit map */}
      {circuitMeta && (
        <div className="mt-10 bg-surface border border-border rounded-2xl p-6">
          <div className="mb-5">
            <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
              Circuit
            </p>
            <h2 className="font-display font-bold text-xl text-ink tracking-tight">
              WHY THIS CIRCUIT MATTERS
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-[2fr_3fr] gap-6 items-start">
            {/* Track image */}
            <div className="bg-ground border border-border rounded-xl p-4 flex items-center justify-center min-h-[130px]">
              {!imgError && circuitMeta.trackImgUrl ? (
                <img
                  src={circuitMeta.trackImgUrl}
                  alt={`${officialName} circuit map`}
                  className="max-h-36 w-full object-contain"
                  onError={() => setImgError(true)}
                />
              ) : (
                <p className="font-body text-sm text-muted text-center">Circuit map unavailable.</p>
              )}
            </div>

            {/* Circuit info */}
            <div>
              <h3 className="font-display font-bold text-lg text-ink tracking-tight mb-1">
                {officialName.toUpperCase()}
              </h3>
              <p className="font-label text-sm text-muted mb-4">{circuitName}</p>
              {overtakingCfg && (
                <div
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-label font-semibold tracking-widest uppercase mb-4"
                  style={{
                    color: overtakingCfg.color,
                    backgroundColor: overtakingCfg.bg,
                    border: `1px solid ${overtakingCfg.border}`,
                  }}
                >
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: overtakingCfg.color }}
                    aria-hidden="true"
                  />
                  Overtaking: {overtakingCfg.label.replace(' Overtaking', '')}
                </div>
              )}
              {circuitMeta.blurb && (
                <p className="font-body text-sm text-ink leading-relaxed">
                  {circuitMeta.blurb}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Idle explainer (qualifying done, no prediction yet) ──────────────────────

function IdleExplainer() {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16">
      <div className="max-w-xl mx-auto text-center mb-14">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-3">
          How it works
        </p>
        <h2 className="font-display font-bold text-2xl text-ink tracking-tight mb-3">
          A PRE-RACE PREDICTION SYSTEM
        </h2>
        <p className="font-body text-fluid-lead text-muted">
          Qualifying sets the starting point. Once the grid is confirmed, hit PREDICT
          to see where the model expects each driver to finish.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            step: '01',
            title: 'Qualifying data',
            body: 'The model takes the confirmed qualifying grid as its starting point — the same data every team and fan uses.',
          },
          {
            step: '02',
            title: 'Season form & pace',
            body: 'Championship standings, constructor rank, and FP2 pace are combined with circuit-specific historical effects.',
          },
          {
            step: '03',
            title: 'Predicted order',
            body: 'A two-stage Ridge regression model outputs a predicted finishing order with position-by-position movement analysis.',
          },
        ].map(({ step, title, body }) => (
          <div key={step} className="bg-surface border border-border rounded-xl p-6">
            <span className="font-display font-black text-3xl text-accent/20 block mb-3">
              {step}
            </span>
            <h3 className="font-label font-bold text-base text-ink mb-2">{title}</h3>
            <p className="font-body text-sm text-muted leading-relaxed">{body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function RacesPage() {
  const [races, setRaces] = useState<RaceEntry[]>([])
  const [selectedRace, setSelectedRace] = useState<string>('')
  const [appState, setAppState] = useState<AppState>({ phase: 'idle' })
  const [racesLoading, setRacesLoading] = useState(true)
  const [racesError, setRacesError] = useState<string | null>(null)
  const [lastRaceStatus, setLastRaceStatus] = useState<LastRaceStatus>({ phase: 'idle' })

  function loadPrediction(name: string) {
    setAppState({ phase: 'loading', race: name, year: YEAR })
    fetchPrediction(name, YEAR)
      .then(data => setAppState({ phase: 'success', data }))
      .catch(err => {
        if (err instanceof ApiError && err.status === 404) {
          setAppState({ phase: 'pre-qualifying', race: name, year: YEAR })
        } else {
          setAppState({ phase: 'error', message: (err as Error).message ?? 'Prediction failed.' })
        }
      })
  }

  useEffect(() => {
    fetchRaces(YEAR)
      .then(data => {
        setRaces(data)
        const current = data.find(r => r.status === 'current') ?? data[data.length - 1]
        if (current) {
          setSelectedRace(current.name)
          const state = stateForRace(current, current.name)
          if (state.phase === 'idle') {
            loadPrediction(current.name)
          } else {
            setAppState(state)
          }
        }
      })
      .catch(err => {
        setRacesError((err as Error).message ?? 'Could not load race schedule.')
      })
      .finally(() => setRacesLoading(false))
  }, [])

  // Find the most recent completed race before the currently selected race.
  const previousRace = useMemo<RaceEntry | null>(() => {
    if (appState.phase !== 'pre-qualifying') return null
    const currentRound = races.find(r => r.name === selectedRace)?.round ?? 999
    const completed = races.filter(
      r => r.status === 'completed' && r.round < currentRound,
    )
    return completed[completed.length - 1] ?? null
  }, [appState.phase, races, selectedRace])

  // Load previous race data whenever a valid previous race is identified.
  useEffect(() => {
    if (!previousRace) {
      setLastRaceStatus({ phase: 'idle' })
      return
    }
    setLastRaceStatus({ phase: 'loading' })
    fetchPrediction(previousRace.name, YEAR)
      .then(data => setLastRaceStatus({ phase: 'loaded', data }))
      .catch(() => setLastRaceStatus({ phase: 'error' }))
  }, [previousRace])

  function handleRaceChange(raceName: string) {
    setSelectedRace(raceName)
    const newRace = races.find(r => r.name === raceName)
    if (newRace) {
      const state = stateForRace(newRace, raceName)
      if (state.phase === 'idle') {
        loadPrediction(raceName)
      } else {
        setAppState(state)
      }
    } else {
      setAppState({ phase: 'idle' })
    }
  }

  function handlePredict() {
    if (!selectedRace) return
    loadPrediction(selectedRace)
  }

  // Navigate to the previous race and show its full completed-race view.
  function handleViewPreviousRace() {
    if (!previousRace) return
    setSelectedRace(previousRace.name)
    loadPrediction(previousRace.name)
  }

  if (racesError) {
    return (
      <ErrorState
        message={`Could not load race schedule: ${racesError}`}
        onRetry={() => window.location.reload()}
      />
    )
  }

  const isPreQualifying = appState.phase === 'pre-qualifying'

  return (
    <div className="min-h-screen bg-bg">
      {races.length > 0 && (
        <RaceHeader
          races={races}
          selectedRace={selectedRace}
          year={YEAR}
          onRaceChange={handleRaceChange}
          onPredict={handlePredict}
          loading={appState.phase === 'loading'}
          hasPrediction={appState.phase === 'success'}
          isPreQualifying={isPreQualifying}
        />
      )}

      {appState.phase === 'idle' && !racesLoading && <IdleExplainer />}

      {appState.phase === 'pre-qualifying' && (
        <PreQualifyingState
          race={appState.race}
          previousRace={previousRace}
          lastRaceStatus={lastRaceStatus}
          onViewPreviousRace={handleViewPreviousRace}
        />
      )}

      {appState.phase === 'loading' && (
        <LoadingState race={appState.race} year={appState.year} />
      )}

      {appState.phase === 'error' && (
        <ErrorState message={appState.message} onRetry={handlePredict} />
      )}

      {appState.phase === 'success' && (
        <>
          {appState.data.is_completed ? (
            // ── COMPLETED RACE: dashboard layout ─────────────────────────────
            <>
              <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <RaceSummaryPanel data={appState.data} />
                  <PerformancePanel data={appState.data} />
                </div>
              </div>
              <CircuitContext data={appState.data} />
              <ActualVsPredicted predictions={appState.data.predictions} />
              <RaceStory predictions={appState.data.predictions} />
            </>
          ) : (
            // ── PRE-RACE: prediction analysis ─────────────────────────────────
            <>
              <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <PredictionSummaryPanel data={appState.data} />
                  <PredictionContextPanel data={appState.data} />
                </div>
              </div>
              <CircuitContext data={appState.data} />
              <WhyPrediction predictions={appState.data.predictions} />
              <PredictionTable predictions={appState.data.predictions} />
            </>
          )}
        </>
      )}
    </div>
  )
}
