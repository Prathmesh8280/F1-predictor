// Maps FastF1 3-letter TLAs to display surnames. Falls back to the raw value if
// the driver field is already a full surname or an unknown code.
export const DRIVER_SURNAMES: Record<string, string> = {
  VER: 'Verstappen', NOR: 'Norris',    PIA: 'Piastri',   LEC: 'Leclerc',
  HAM: 'Hamilton',   RUS: 'Russell',   ANT: 'Antonelli',  ALO: 'Alonso',
  STR: 'Stroll',     GAS: 'Gasly',     COL: 'Colapinto',  ALB: 'Albon',
  SAI: 'Sainz',      TSU: 'Tsunoda',   HAD: 'Hadjar',     HUL: 'Hülkenberg',
  BOR: 'Bortoleto',  OCO: 'Ocon',      BEA: 'Bearman',    HER: 'Herta',
  LAW: 'Lawson',     DOO: 'Doohan',    MAG: 'Magnussen',  BOT: 'Bottas',
  ZHO: 'Zhou',       PER: 'Pérez',     SAR: 'Sargeant',   DEV: 'de Vries',
}

export function driverDisplay(code: string): string {
  if (code.length === 3) return DRIVER_SURNAMES[code.toUpperCase()] ?? code
  return code
}
