export interface PredictionRow {
  rank: number
  driver: string
  team: string
  grid_pos: number
  actual_rank: number | null
  // Model signals — null when not available (e.g. standings on Round 1)
  championship_rank: number | null
  constructor_rank: number | null
  fp2_pace_rank: number | null
  delta1: number | null
  stage2_used: boolean
}

export interface CircuitInfo {
  name: string
  country_code: string
  overtaking: 'VERY HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'VERY LOW'
  track_img_url: string
}

export interface PredictionResponse {
  race: string
  year: number
  circuit: CircuitInfo
  predictions: PredictionRow[]
  is_completed: boolean
  model_mae: number | null
  baseline_mae: number | null
}

export interface RaceEntry {
  name: string
  round: number
  date: string
  status: 'completed' | 'current'
}

export type AppState =
  | { phase: 'idle' }
  | { phase: 'pre-qualifying'; race: string; year: number }
  | { phase: 'loading'; race: string; year: number }
  | { phase: 'success'; data: PredictionResponse }
  | { phase: 'error'; message: string }
