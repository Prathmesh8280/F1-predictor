import { useState } from 'react'
import type { PredictionResponse } from '../../types'
import { CIRCUIT_META, OVERTAKING_CONFIG } from '../../constants/races'

interface CircuitContextProps {
  data: PredictionResponse
}

export default function CircuitContext({ data }: CircuitContextProps) {
  const [imgError, setImgError] = useState(false)
  const meta = CIRCUIT_META[data.race]

  // Use circuit info from API, fallback to CIRCUIT_META
  const circuitInfo = data.circuit
  const overtakingRating = meta?.overtaking ?? (circuitInfo.overtaking as typeof meta.overtaking)
  const overtakingCfg = overtakingRating ? OVERTAKING_CONFIG[overtakingRating] : null
  const blurb = meta?.blurb ?? ''
  const circuitName = meta?.name ?? circuitInfo.name
  const officialName = meta?.officialName ?? `${data.race} Grand Prix`
  const imgUrl = meta?.trackImgUrl ?? circuitInfo.track_img_url

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 border-t border-border">
      <div className="bg-surface border border-border rounded-2xl p-6">
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
          {!imgError && imgUrl ? (
            <div className="bg-ground border border-border rounded-xl p-4 flex items-center justify-center min-h-[130px]">
              <img
                src={imgUrl}
                alt={`${officialName} circuit map`}
                className="max-h-36 w-full object-contain"
                onError={() => setImgError(true)}
              />
            </div>
          ) : (
            <div className="bg-ground border border-border rounded-xl p-4 flex items-center justify-center min-h-[130px]">
              <p className="font-body text-sm text-muted text-center">Circuit map unavailable.</p>
            </div>
          )}

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

            {blurb && (
              <p className="font-body text-sm text-ink leading-relaxed">
                {blurb}
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
