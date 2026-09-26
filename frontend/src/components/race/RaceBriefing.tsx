import type { PredictionResponse } from '../../types'
import { raceBriefing } from '../../lib/predictionBriefing'

interface Props {
  data: PredictionResponse
}

export default function RaceBriefing({ data }: Props) {
  const text = raceBriefing(data.predictions, data.circuit)
  if (!text) return null

  return (
    <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-8">
      <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-2">
        The Briefing
      </p>
      <p className="font-body text-fluid-lead text-ink leading-relaxed max-w-3xl">
        {text}{' '}
        <a
          href="/new-to-f1"
          className="text-accent/70 hover:text-accent underline underline-offset-2"
        >
          New to these terms? Read the F1 basics →
        </a>
      </p>
    </section>
  )
}
