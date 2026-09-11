import { useEffect, useRef, useState } from 'react'

/**
 * Reports when an element scrolls into the viewport, so animations can fire
 * when the user actually sees them rather than on mount (when they may be
 * below the fold). Fires once by default. Falls back to `true` if
 * IntersectionObserver is unavailable, so content is never stuck hidden.
 */
export function useInView<T extends HTMLElement>(
  opts: { once?: boolean; rootMargin?: string; threshold?: number } = {},
) {
  const { once = true, rootMargin = '0px 0px -12% 0px', threshold = 0.2 } = opts
  const ref = useRef<T>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (typeof IntersectionObserver === 'undefined') {
      setInView(true)
      return
    }
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          if (once) obs.disconnect()
        } else if (!once) {
          setInView(false)
        }
      },
      { rootMargin, threshold },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [once, rootMargin, threshold])

  return [ref, inView] as const
}
