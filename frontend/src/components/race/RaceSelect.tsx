import { useEffect, useMemo, useRef, useState } from 'react'
import type { RaceEntry } from '../../types'
import { CIRCUIT_META } from '../../constants/races'
import { driverDisplay } from '../../constants/drivers'

type StatusTone = 'completed' | 'accent' | 'muted'

interface RaceSelectProps {
  races: RaceEntry[]
  selectedRace: string
  onRaceChange: (race: string) => void
  disabled?: boolean
  statusLabel?: string
  statusTone?: StatusTone
}

const TONE_CLS: Record<StatusTone, string> = {
  completed: 'bg-positive/10 text-positive',
  accent: 'bg-accent/10 text-accent',
  muted: 'bg-muted/10 text-muted',
}

function flagUrl(countryCode: string): string {
  return `https://flagcdn.com/w40/${countryCode.toLowerCase()}.png`
}

function fmtDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function Flag({ code }: { code?: string }) {
  if (!code) return <span className="w-6 shrink-0" />
  return (
    <img
      src={flagUrl(code)}
      alt=""
      width={24}
      height={18}
      loading="lazy"
      className="w-6 h-[18px] rounded-[2px] object-cover shrink-0 border border-border"
      onError={e => {
        e.currentTarget.style.visibility = 'hidden'
      }}
    />
  )
}

function StatusPill({ label, tone }: { label: string; tone: StatusTone }) {
  return (
    <span
      className={`font-label font-bold text-[9px] tracking-widest uppercase px-2 py-1 rounded-full whitespace-nowrap ${TONE_CLS[tone]}`}
    >
      {label}
    </span>
  )
}

export default function RaceSelect({
  races,
  selectedRace,
  onRaceChange,
  disabled,
  statusLabel,
  statusTone = 'muted',
}: RaceSelectProps) {
  const [open, setOpen] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const rootRef = useRef<HTMLDivElement>(null)

  // Presentation order: most recent / current race first.
  const ordered = useMemo(
    () => [...races].sort((a, b) => b.round - a.round),
    [races],
  )

  useEffect(() => {
    if (!open) return
    function onDocClick(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [open])

  // When opening, focus the currently selected row.
  useEffect(() => {
    if (open) {
      setActiveIdx(ordered.findIndex(r => r.name === selectedRace))
    }
  }, [open, ordered, selectedRace])

  const selected = races.find(r => r.name === selectedRace)
  const selectedMeta = selected ? CIRCUIT_META[selected.name] : undefined

  function pick(name: string) {
    onRaceChange(name)
    setOpen(false)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      setOpen(false)
      return
    }
    if (!open && (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault()
      setOpen(true)
      return
    }
    if (!open) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx(i => Math.min(i + 1, ordered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (activeIdx >= 0 && ordered[activeIdx]) pick(ordered[activeIdx].name)
    }
  }

  return (
    <div ref={rootRef} className="relative w-full sm:w-[360px]" onKeyDown={onKeyDown}>
      {/* Collapsed trigger — navigation only, no date/winner */}
      <button
        type="button"
        onClick={() => !disabled && setOpen(o => !o)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select race"
        className="w-full flex items-center gap-2.5 bg-surface border border-border rounded-lg px-3 py-2.5 hover:border-accent focus-visible:border-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {selected ? (
          <>
            <Flag code={selectedMeta?.countryCode} />
            <span className="font-data font-bold text-sm text-muted leading-none">
              R{selected.round}
            </span>
            <span className="font-label font-semibold text-sm text-ink truncate flex-1 text-left leading-none relative top-[1px]">
              {selected.name}
            </span>
            {statusLabel && <StatusPill label={statusLabel} tone={statusTone} />}
          </>
        ) : (
          <span className="flex-1 text-left font-label text-sm text-muted">
            Select race
          </span>
        )}
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          className={`shrink-0 text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="currentColor"
        >
          <path d="M6 8L1 3h10z" />
        </svg>
      </button>

      {/* Expanded list */}
      {open && (
        <div
          role="listbox"
          className="absolute z-30 mt-2 w-full max-h-[360px] overflow-y-auto bg-surface border border-border rounded-xl shadow-lg shadow-ink/5"
        >
          {ordered.map((r, idx) => {
            const isSel = r.name === selectedRace
            const isActive = idx === activeIdx
            const meta = CIRCUIT_META[r.name]
            const winnerLine =
              r.status === 'completed' && r.winner
                ? `${fmtDate(r.date)} · Winner ${driverDisplay(r.winner)}`
                : fmtDate(r.date)
            return (
              <button
                key={r.name}
                type="button"
                role="option"
                aria-selected={isSel}
                onMouseEnter={() => setActiveIdx(idx)}
                onClick={() => pick(r.name)}
                className={`w-full text-left pr-3.5 py-2.5 border-b border-border last:border-b-0 border-l-2 transition-colors ${
                  isSel
                    ? 'bg-[#F1F1EF] border-l-accent'
                    : `border-l-transparent ${isActive ? 'bg-ground' : ''}`
                }`}
              >
                <div className="grid grid-cols-[auto_2rem_1fr_auto] items-center gap-2.5 min-w-0 pl-3">
                  <Flag code={meta?.countryCode} />
                  <span className="font-data font-bold text-sm text-muted text-center">
                    R{r.round}
                  </span>
                  <div className="min-w-0">
                    <div className="font-label font-semibold text-sm text-ink truncate">
                      {r.name}
                    </div>
                    <div className="font-body text-[11px] text-muted truncate">
                      {winnerLine}
                    </div>
                  </div>
                  {r.status === 'current' ? (
                    <span className="font-label font-bold text-[9px] tracking-widest uppercase px-2 py-1 rounded-full whitespace-nowrap bg-accent/10 text-accent">
                      This Week
                    </span>
                  ) : isSel ? (
                    <span className="font-label font-bold text-[9px] tracking-widest uppercase text-muted whitespace-nowrap">
                      Selected
                    </span>
                  ) : null}
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
