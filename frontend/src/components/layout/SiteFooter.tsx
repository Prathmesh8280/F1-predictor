import { Github, Linkedin } from 'lucide-react'

export default function SiteFooter() {
  return (
    <footer className="border-t border-border bg-surface mt-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-col items-center md:items-start gap-1">
            <span className="font-display font-bold text-sm tracking-widest text-ink">
              F1 RACE PREDICTOR
            </span>
            <span className="font-body text-xs text-muted">
              Built by Prathmesh Bargal
            </span>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="https://github.com/Prathmesh8280/F1-predictor"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 font-label text-xs text-muted hover:text-ink transition-colors focus-visible:outline-accent"
              aria-label="GitHub repository"
            >
              <Github size={14} />
              GitHub
            </a>
            <span className="text-border">·</span>
            <a
              href="https://www.linkedin.com/in/prathmesh-bargal-9b311a237/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 font-label text-xs text-muted hover:text-ink transition-colors focus-visible:outline-accent"
              aria-label="LinkedIn profile"
            >
              <Linkedin size={14} />
              LinkedIn
            </a>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-border text-center">
          <p className="font-body text-[11px] text-muted">
            Data via FastF1 · Pre-race prediction · No live race data
          </p>
        </div>
      </div>
    </footer>
  )
}
