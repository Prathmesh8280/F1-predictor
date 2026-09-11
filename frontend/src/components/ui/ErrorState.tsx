interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] px-6 text-center">
      <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-negative mb-2">
        Error
      </p>
      <h2 className="font-display font-bold text-2xl text-ink tracking-tight mb-3">
        PREDICTION UNAVAILABLE
      </h2>
      <p className="font-body text-base text-muted max-w-sm mb-6">
        {message || "We couldn't generate this race prediction right now."}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="font-label font-semibold text-sm tracking-widest uppercase bg-accent text-white px-6 py-3 rounded-lg hover:bg-accent-dark transition-colors focus-visible:outline-accent"
        >
          Try Again
        </button>
      )}
    </div>
  )
}
