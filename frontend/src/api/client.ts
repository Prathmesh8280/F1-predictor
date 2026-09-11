import type { PredictionResponse, RaceEntry } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function fetchRaces(year = 2026): Promise<RaceEntry[]> {
  const res = await fetch(`${API_BASE}/races?year=${year}`)
  if (!res.ok) throw new Error(`Could not load race schedule (${res.status})`)
  return res.json()
}

export async function fetchPrediction(
  race: string,
  year: number,
  forceRefresh = false,
): Promise<PredictionResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ race, year, force_refresh: forceRefresh }),
  })

  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body.detail) detail = body.detail
    } catch {}
    throw new ApiError(detail, res.status)
  }

  return res.json()
}
