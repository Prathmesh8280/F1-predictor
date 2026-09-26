import type { PredictionResponse } from '../../types'
import { raceStoryNarrative } from '../../lib/predictionBriefing'

interface Props {
  data: PredictionResponse
}

export default function RaceStory({ data }: Props) {
  const text = raceStoryNarrative(data.predictions)
  if (!text) return null

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 py-8 border-t border-border">
      <div className="mb-4">
        <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-1">
          Analysis
        </p>
        <h2 className="font-display font-bold text-xl text-ink tracking-tight">
          RACE STORY
        </h2>
      </div>
      <p className="font-body text-fluid-lead text-ink leading-relaxed max-w-3xl">
        {text}
      </p>
    </section>
  )
}
