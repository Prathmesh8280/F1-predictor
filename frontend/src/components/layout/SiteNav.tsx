import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, X } from 'lucide-react'

const NAV_LINKS = [
  { to: '/', label: 'RACES' },
  { to: '/how-it-works', label: 'HOW IT WORKS' },
  { to: '/about', label: 'ABOUT' },
]

export default function SiteNav() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 bg-topbar border-b border-white/10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        {/* Logo */}
        <NavLink
          to="/"
          className="flex items-center gap-2 focus-visible:outline-accent"
          aria-label="F1 Race Predictor home"
          onClick={() => setOpen(false)}
        >
          <span className="w-1 h-5 bg-accent rounded-full" aria-hidden="true" />
          <span className="font-display font-bold text-sm tracking-widest text-white">
            F1 RACE PREDICTOR
          </span>
        </NavLink>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6" aria-label="Site navigation">
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `font-label font-semibold text-xs tracking-widest transition-colors ${
                  isActive ? 'text-white' : 'text-white/45 hover:text-white/75'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-white/70 hover:text-white p-1 rounded focus-visible:outline-accent"
          onClick={() => setOpen(v => !v)}
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <nav
          className="md:hidden bg-topbar border-t border-white/10 px-4 py-4 flex flex-col gap-4"
          aria-label="Mobile navigation"
        >
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `font-label font-semibold text-sm tracking-widest py-2 border-b border-white/10 transition-colors ${
                  isActive ? 'text-white' : 'text-white/50 hover:text-white/80'
                }`
              }
              onClick={() => setOpen(false)}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}
