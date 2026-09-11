import { Github, Linkedin } from 'lucide-react'
import { Link } from 'react-router-dom'

const GITHUB_URL = 'https://github.com/Prathmesh8280/F1-predictor'
const LINKEDIN_URL = 'https://www.linkedin.com/in/prathmesh-bargal-9b311a237/'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-bg">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className="bg-topbar text-white py-16 sm:py-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-6">
            About F1 Race Predictor
          </p>
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-white/40 mb-2">
            Built by
          </p>
          <h1 className="font-display font-black text-4xl sm:text-6xl tracking-tight text-white mb-6 leading-none">
            PRATHMESH BARGAL
          </h1>
          <p className="font-body text-fluid-lead text-white/60 max-w-lg mb-10">
            I'm a Data &amp; AI professional interested in machine learning,
            sports analytics, and building things around data.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 font-label font-semibold text-sm tracking-widest uppercase bg-white text-topbar px-5 py-2.5 rounded-lg hover:bg-white/90 transition-colors focus-visible:outline-accent"
              aria-label="View project on GitHub"
            >
              <Github size={16} />
              GitHub
            </a>
            <a
              href={LINKEDIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 font-label font-semibold text-sm tracking-widest uppercase text-white/70 border border-white/20 px-5 py-2.5 rounded-lg hover:text-white hover:border-white/50 transition-colors focus-visible:outline-accent"
              aria-label="Connect on LinkedIn"
            >
              <Linkedin size={16} />
              LinkedIn
            </a>
          </div>
        </div>
      </div>

      {/* ── Body ──────────────────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6">

        {/* Why I Built This */}
        <section className="py-14 border-b border-border">
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-5">
            Why I Built This
          </p>
          <p className="font-body text-lg text-ink leading-relaxed mb-4">
            This started as a machine learning experiment — could you predict an F1 race
            finishing order using only pre-race information?
          </p>
          <p className="font-body text-base text-muted leading-relaxed">
            But I wanted to take it further. From a model running on a dataset to something
            people could actually use on an F1 race weekend. That meant thinking beyond
            notebooks and metrics — about the product, the experience, and how someone
            who cares about F1 would actually want to interact with a prediction.
          </p>
        </section>

        {/* Why F1 */}
        <section className="py-14 border-b border-border">
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-5">
            Why F1?
          </p>
          <p className="font-display font-bold text-2xl text-ink tracking-tight leading-snug mb-6">
            Qualifying tells us where every driver starts.<br />
            The interesting question is where they finish.
          </p>
          <p className="font-body text-base text-muted leading-relaxed">
            F1 sits at an interesting intersection — sport, statistics, uncertainty, and
            performance. There's a grid position. There's a finishing position. Between
            those two numbers sit 50+ laps, 20 drivers, tire strategies, and randomness.
            That gap is exactly where prediction becomes interesting.
          </p>
        </section>

        {/* Beyond F1 */}
        <section className="py-14 border-b border-border">
          <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-5">
            Beyond F1
          </p>
          <p className="font-body text-sm text-muted mb-6">
            Other things I think about:
          </p>
          <div className="flex flex-wrap gap-2">
            {[
              'Data & AI',
              'Sports analytics',
              'Cricket',
              'Baseball',
              'Statistics',
              'Poker',
            ].map(interest => (
              <span
                key={interest}
                className="font-label font-semibold text-sm text-ink border border-border rounded-full px-4 py-1.5"
              >
                {interest}
              </span>
            ))}
          </div>
        </section>

        {/* Keep Exploring + Get in Touch */}
        <section className="py-14">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-10">

            <div>
              <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-4">
                Keep Exploring
              </p>
              <p className="font-body text-sm text-muted leading-relaxed mb-5">
                Want to understand how the predictions are made — the data, the model,
                and what it can and can't predict?
              </p>
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 font-label font-semibold text-sm tracking-widest uppercase text-ink border border-border px-5 py-2.5 rounded-lg hover:border-ink transition-colors focus-visible:outline-accent"
              >
                Explore How It Works →
              </Link>
            </div>

            <div>
              <p className="font-label font-semibold text-[11px] tracking-widest uppercase text-accent mb-4">
                Get in Touch
              </p>
              <p className="font-body text-sm text-muted leading-relaxed mb-5">
                Have an idea, spotted something interesting in the results,
                or just want to talk F1 and data?
              </p>
              <a
                href={LINKEDIN_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 font-label font-semibold text-sm tracking-widest uppercase bg-topbar text-white px-5 py-2.5 rounded-lg hover:bg-ink transition-colors focus-visible:outline-accent"
                aria-label="Connect on LinkedIn"
              >
                <Linkedin size={15} />
                Connect on LinkedIn →
              </a>
            </div>

          </div>
        </section>

      </div>
    </div>
  )
}
