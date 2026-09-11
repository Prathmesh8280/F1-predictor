import { useEffect, useRef, useState } from 'react'

/**
 * Counts a number up from 0 to `target`, starting when `active` becomes true
 * (e.g. when the element scrolls into view). Exponential ease-out so it
 * decelerates into the final value. Respects the OS reduce-motion setting by
 * jumping straight to the target.
 */
export function useCountUp(target: number, durationMs = 700, active = true): number {
  const [value, setValue] = useState(active ? target : 0)
  const rafRef = useRef<number>()

  useEffect(() => {
    if (!active) return
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduce || target === 0) {
      setValue(target)
      return
    }

    let start: number | null = null
    const tick = (t: number) => {
      if (start === null) start = t
      const p = Math.min((t - start) / durationMs, 1)
      const eased = 1 - Math.pow(1 - p, 3) // ease-out cubic
      setValue(target * eased)
      if (p < 1) rafRef.current = requestAnimationFrame(tick)
      else setValue(target)
    }
    rafRef.current = requestAnimationFrame(tick)

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [target, durationMs, active])

  return value
}
