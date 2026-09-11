export const TEAM_COLORS: Record<string, string> = {
  'Red Bull Racing': '#3671C6',
  Ferrari: '#E8002D',
  McLaren: '#FF8000',
  Mercedes: '#27F4D2',
  'Aston Martin': '#229971',
  Alpine: '#FF87BC',
  Williams: '#64C4FF',
  'Racing Bulls': '#6692FF',
  RB: '#6692FF',
  'Kick Sauber': '#52E252',
  'Haas F1 Team': '#B6BABD',
  Cadillac: '#C8A000',
  Audi: '#BB0000',
}

export const TEAM_CODES: Record<string, string> = {
  'Red Bull Racing': 'RBR',
  Ferrari: 'FER',
  McLaren: 'MCL',
  Mercedes: 'MER',
  'Aston Martin': 'AMR',
  Alpine: 'ALP',
  Williams: 'WIL',
  'Racing Bulls': 'RBF',
  RB: 'RBF',
  'Kick Sauber': 'SAU',
  'Haas F1 Team': 'HAS',
  Cadillac: 'CAD',
  Audi: 'AUD',
}

export const TEAM_SLUGS: Record<string, string> = {
  'Red Bull Racing': 'red-bull',
  Ferrari: 'ferrari',
  McLaren: 'mclaren',
  Mercedes: 'mercedes',
  'Aston Martin': 'aston-martin',
  Alpine: 'alpine',
  Williams: 'williams',
  'Racing Bulls': 'rb',
  RB: 'rb',
  'Kick Sauber': 'kick-sauber',
  'Haas F1 Team': 'haas',
  Cadillac: 'cadillac',
  Audi: 'audi',
}

export const DEFAULT_TEAM_COLOR = '#888888'

export function teamColor(team: string): string {
  for (const [key, color] of Object.entries(TEAM_COLORS)) {
    if (key.toLowerCase().includes(team.toLowerCase()) || team.toLowerCase().includes(key.toLowerCase())) {
      return color
    }
  }
  return DEFAULT_TEAM_COLOR
}

export function teamCode(team: string): string {
  for (const [key, code] of Object.entries(TEAM_CODES)) {
    if (key.toLowerCase().includes(team.toLowerCase()) || team.toLowerCase().includes(key.toLowerCase())) {
      return code
    }
  }
  return team.slice(0, 3).toUpperCase()
}

export function teamSlug(team: string): string {
  for (const [key, slug] of Object.entries(TEAM_SLUGS)) {
    if (key.toLowerCase().includes(team.toLowerCase()) || team.toLowerCase().includes(key.toLowerCase())) {
      return slug
    }
  }
  return ''
}

export const PODIUM_COLORS: Record<number, string> = {
  1: '#D4AF37',
  2: '#A8A9AD',
  3: '#CD7F32',
}
