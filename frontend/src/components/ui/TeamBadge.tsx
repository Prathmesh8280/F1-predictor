import { useState } from 'react'
import { teamSlug, teamColor } from '../../constants/teamColors'

interface TeamBadgeProps {
  team: string
  /** Tailwind size classes applied to the outer badge, e.g. "w-6 h-6" */
  className?: string
}

export default function TeamBadge({ team, className = 'w-6 h-6' }: TeamBadgeProps) {
  const [failed, setFailed] = useState(false)
  const slug = teamSlug(team)
  const color = teamColor(team)

  // Always render as a colored badge — keeps logos visible on any page background
  return (
    <span
      className={`${className} rounded-md flex-shrink-0 flex items-center justify-center overflow-hidden`}
      style={{ backgroundColor: color }}
      title={team}
    >
      {!failed && slug ? (
        <img
          src={`/teams/${slug}.webp`}
          alt={team}
          className="w-full h-full object-contain p-0.5"
          onError={() => setFailed(true)}
        />
      ) : (
        // Fallback: team initials in contrasting colour
        <span
          className="font-data font-black text-[8px] leading-none select-none"
          style={{ color: isLight(color) ? '#18181B' : '#FFFFFF' }}
          aria-label={team}
        >
          {slug.slice(0, 3).toUpperCase() || team.slice(0, 3).toUpperCase()}
        </span>
      )}
    </span>
  )
}

function isLight(hex: string): boolean {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return (r * 299 + g * 587 + b * 114) / 1000 > 128
}
