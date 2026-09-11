interface LoadingStateProps {
  race?: string
  year?: number
}

export default function LoadingState({ race, year }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      {/* Spinner */}
      <div
        className="w-10 h-10 rounded-full border-2 border-border border-t-accent animate-spin_smooth mb-8"
        role="status"
        aria-label="Loading"
      />

      <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-2">
        Analyzing the grid
      </p>
      <h2 className="font-display font-bold text-2xl text-ink tracking-tight mb-1">
        GENERATING PREDICTION
      </h2>
      {race && (
        <p className="font-body text-base text-muted mt-2">
          {race}{year ? ` · ${year}` : ''}
        </p>
      )}
      <p className="font-body text-sm text-muted mt-6 max-w-xs">
        First load may take 30–60 seconds while the model runs.
      </p>
    </div>
  )
}
