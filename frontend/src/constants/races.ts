const F1 = (slug: string) =>
  `https://media.formula1.com/image/upload/c_fit,h_704/q_auto/v1740000001/common/f1/2026/track/2026track${slug}detailed.webp`

export interface CircuitMeta {
  countryCode: string
  name: string
  officialName: string
  overtaking: 'VERY HIGH' | 'HIGH' | 'MEDIUM' | 'LOW' | 'VERY LOW'
  blurb: string
  trackImgUrl: string
  round2026?: number
}

export const CIRCUIT_META: Record<string, CircuitMeta> = {
  Australia: {
    countryCode: 'au',
    name: 'Albert Park, Melbourne',
    officialName: 'Australian Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 1,
    blurb: 'A street-park circuit built around a lake in Melbourne. The long main straight rewards top speed and slipstreaming, but the narrow layout makes overtaking hard without DRS. Track position from qualifying is valuable.',
    trackImgUrl: F1('melbourne'),
  },
  China: {
    countryCode: 'cn',
    name: 'Shanghai International Circuit',
    officialName: 'Chinese Grand Prix',
    overtaking: 'HIGH',
    round2026: 2,
    blurb: 'Two long straights and wide braking zones still create genuine passing opportunities. In 2026 the slipstream effect replaces DRS as the main overtaking tool — cars with strong straight-line speed can work through the field from mid-grid.',
    trackImgUrl: F1('shanghai'),
  },
  Japan: {
    countryCode: 'jp',
    name: 'Suzuka Circuit',
    officialName: 'Japanese Grand Prix',
    overtaking: 'LOW',
    round2026: 3,
    blurb: 'A technical figure-8 layout famous for fast, flowing corners and very few natural passing spots. Without DRS to help down the main straight, overtaking here is even rarer — a clean qualifying lap is essential.',
    trackImgUrl: F1('suzuka'),
  },
  Bahrain: {
    countryCode: 'bh',
    name: 'Bahrain International Circuit',
    officialName: 'Bahrain Grand Prix',
    overtaking: 'HIGH',
    round2026: 16,
    blurb: 'Several long braking zones and slow-speed corners create genuine wheel-to-wheel moments. Without DRS the balance shifts toward mechanical grip and tyre management, but Bahrain remains one of the most overtaking-friendly venues on the calendar.',
    trackImgUrl: F1('bahrain'),
  },
  'Saudi Arabia': {
    countryCode: 'sa',
    name: 'Jeddah Corniche Circuit',
    officialName: 'Saudi Arabian Grand Prix',
    overtaking: 'MEDIUM',
    round2026: undefined,
    blurb: 'An ultra-fast street circuit where safety cars appear regularly and the barriers are unforgiving. Without DRS, the long Jeddah straight becomes a pure slipstream and engine-power test. Strategy and timing matter as much as qualifying pace.',
    trackImgUrl: F1('jeddah'),
  },
  Miami: {
    countryCode: 'us',
    name: 'Miami International Autodrome',
    officialName: 'Miami Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 4,
    blurb: 'A purpose-built street-style circuit with a mix of slow and fast sections. The active aero system helps on the main straight but the tight infield limits passing. Consistent tyre management tends to decide results.',
    trackImgUrl: F1('miami'),
  },
  Canada: {
    countryCode: 'ca',
    name: 'Circuit Gilles Villeneuve',
    officialName: 'Canadian Grand Prix',
    overtaking: 'HIGH',
    round2026: 5,
    blurb: "A wall-lined circuit with a long pit straight leading into the famous hairpin. One of F1's classic overtaking venues — the slipstream down the straight remains potent in 2026 and the heavy braking zone creates late-dive opportunities.",
    trackImgUrl: F1('canada'),
  },
  Monaco: {
    countryCode: 'mc',
    name: 'Circuit de Monaco',
    officialName: 'Monaco Grand Prix',
    overtaking: 'VERY LOW',
    round2026: 6,
    blurb: 'The most famous race in the world through the narrow streets of Monte Carlo. Overtaking is virtually impossible — arguably even more so in 2026 without DRS. Qualifying position and strategy under safety cars is everything.',
    trackImgUrl: F1('montecarlo'),
  },
  Spain: {
    countryCode: 'es',
    name: 'Circuit de Barcelona-Catalunya',
    officialName: 'Barcelona Grand Prix',
    overtaking: 'LOW',
    round2026: 7,
    blurb: 'A smooth, well-understood circuit that teams know inside out from pre-season testing. Without DRS, passing requires a significant pace gap or a strategic advantage — clean air and track position matter greatly.',
    trackImgUrl: F1('barcelona'),
  },
  Madrid: {
    countryCode: 'es',
    name: 'Ifema Madrid (Madrid Ring)',
    officialName: 'Spanish Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 14,
    blurb: 'A brand-new street circuit built around the Ifema exhibition centre on the outskirts of Madrid. Wider than Monaco with longer straights, the layout offers more natural overtaking than a typical street track. Power and tyre management are expected to be key in 2026.',
    trackImgUrl: F1('madrid'),
  },
  Austria: {
    countryCode: 'at',
    name: 'Red Bull Ring',
    officialName: 'Austrian Grand Prix',
    overtaking: 'HIGH',
    round2026: 8,
    blurb: 'Short and punchy with a strong slipstream opportunity on the main straight. The 2026 cars\' improved ability to follow closely through the fast final sector helps wheel-to-wheel battles. Tyre wear creates strategic variety.',
    trackImgUrl: F1('austria'),
  },
  Britain: {
    countryCode: 'gb',
    name: 'Silverstone Circuit',
    officialName: 'British Grand Prix',
    overtaking: 'HIGH',
    round2026: 9,
    blurb: 'High-speed corners and a long main straight make Silverstone one of the most exciting venues on the calendar. The 2026 ground-effect cars follow more closely through the fast sweeps, helping close racing. Tyre wear remains a major variable.',
    trackImgUrl: F1('silverstone'),
  },
  Belgium: {
    countryCode: 'be',
    name: 'Circuit de Spa-Francorchamps',
    officialName: 'Belgian Grand Prix',
    overtaking: 'HIGH',
    round2026: 10,
    blurb: "Spa's Kemmel Straight is one of the longest in F1 and raw straight-line power is still the dominant factor. Slipstreaming up the hill replaced DRS as the main overtaking weapon — big power advantages translate directly into position gains.",
    trackImgUrl: F1('spa'),
  },
  Hungary: {
    countryCode: 'hu',
    name: 'Hungaroring',
    officialName: 'Hungarian Grand Prix',
    overtaking: 'VERY LOW',
    round2026: 11,
    blurb: 'Tight and twisty, often compared to Monaco without the barriers. Without DRS on the short straight, passing here is exceptionally difficult. Track position from qualifying is critical and almost never recovered once lost.',
    trackImgUrl: F1('hungary'),
  },
  Netherlands: {
    countryCode: 'nl',
    name: 'Circuit Zandvoort',
    officialName: 'Dutch Grand Prix',
    overtaking: 'VERY LOW',
    round2026: 12,
    blurb: 'Banked corners and a narrow layout leave almost no natural passing spots. Without DRS — which was the main overtaking tool here — Zandvoort becomes one of the hardest tracks on the calendar to gain positions on-track.',
    trackImgUrl: F1('zandvoort'),
  },
  Italy: {
    countryCode: 'it',
    name: 'Autodromo Nazionale Monza',
    officialName: 'Italian Grand Prix',
    overtaking: 'VERY HIGH',
    round2026: 13,
    blurb: "Known as the Temple of Speed. Monza's enormous straights create massive slipstream battles even without DRS — raw engine power and top speed remain the dominant factors. The new 2026 power units make this a fascinating test of electric deployment.",
    trackImgUrl: F1('monza'),
  },
  Azerbaijan: {
    countryCode: 'az',
    name: 'Baku City Circuit',
    officialName: 'Azerbaijan Grand Prix',
    overtaking: 'HIGH',
    round2026: 15,
    blurb: "Baku's main straight is the longest in F1 at over 2km — a pure power and slipstream circuit. Safety cars remain frequent through the narrow castle section, but the loss of DRS makes the straight an even purer test of engine advantage.",
    trackImgUrl: F1('baku'),
  },
  Singapore: {
    countryCode: 'sg',
    name: 'Marina Bay Street Circuit',
    officialName: 'Singapore Grand Prix',
    overtaking: 'VERY LOW',
    round2026: 17,
    blurb: 'A night race through tight city streets where safety cars are near-guaranteed. Without DRS, passing through Singapore\'s narrow sections is extremely difficult. Strategy under safety car conditions and qualifying position is almost everything.',
    trackImgUrl: F1('singapore'),
  },
  'United States': {
    countryCode: 'us',
    name: 'Circuit of the Americas',
    officialName: 'United States Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 18,
    blurb: "Wide runoffs and a long back straight give cars natural room to race. Turn 1 at the top of the hill is a classic late-braking spot. The loss of DRS is partially offset by COTA's naturally wide layout and multiple overtaking zones.",
    trackImgUrl: F1('austin'),
  },
  'Mexico City': {
    countryCode: 'mx',
    name: 'Autodromo Hermanos Rodriguez',
    officialName: 'Mexico City Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 19,
    blurb: "High altitude (2,200m) significantly reduces aerodynamic downforce for all cars. Without DRS, the pace advantage earned in qualifying carries even more directly into the race here. The 2026 electrical power system is less affected by thin air than combustion.",
    trackImgUrl: F1('mexico'),
  },
  Brazil: {
    countryCode: 'br',
    name: 'Interlagos',
    officialName: 'Sao Paulo Grand Prix',
    overtaking: 'HIGH',
    round2026: 20,
    blurb: "Famous for chaotic, unpredictable races. The undulating layout and long back straight create natural overtaking opportunities without needing DRS. Brazilian weather can change rapidly and completely flip the running order.",
    trackImgUrl: F1('saopaulo'),
  },
  'Las Vegas': {
    countryCode: 'us',
    name: 'Las Vegas Strip Circuit',
    officialName: 'Las Vegas Grand Prix',
    overtaking: 'HIGH',
    round2026: 21,
    blurb: 'A Saturday night race along the famous Las Vegas Strip. The enormous straight is a pure power and slipstream test — without DRS, engine advantage matters greatly. The cold night temperatures add a tyre management dimension.',
    trackImgUrl: F1('lasvegas'),
  },
  Qatar: {
    countryCode: 'qa',
    name: 'Lusail International Circuit',
    officialName: 'Qatar Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 22,
    blurb: 'A high-speed flowing circuit where tyre degradation is severe. Without DRS, the race tends to be decided more by strategic pit stop timing and tyre management than outright on-track passing.',
    trackImgUrl: F1('qatar'),
  },
  'Abu Dhabi': {
    countryCode: 'ae',
    name: 'Yas Marina Circuit',
    officialName: 'Abu Dhabi Grand Prix',
    overtaking: 'MEDIUM',
    round2026: 23,
    blurb: "The season finale at Yas Marina. The 2021 layout revision improved racing quality significantly. Without DRS, the circuit relies more on the 2026 active aero and natural pace differences — strategy and tyre timing tend to be the deciding factors.",
    trackImgUrl: F1('abudhabi'),
  },
}

export const RACE_NAMES = Object.keys(CIRCUIT_META)

/** Round number → circuit key for the 2026 season */
export const ROUND_MAP_2026: Record<number, string> = Object.fromEntries(
  Object.entries(CIRCUIT_META)
    .filter(([, v]) => v.round2026 != null)
    .map(([k, v]) => [v.round2026!, k])
)

/** Look up a circuit key by round number (current season) */
export function circuitByRound(round: number): string | undefined {
  return ROUND_MAP_2026[round]
}

export const OVERTAKING_CONFIG = {
  'VERY HIGH': { label: 'Very High Overtaking', color: '#16a34a', bg: 'rgba(22,163,74,0.08)', border: 'rgba(22,163,74,0.2)' },
  HIGH:        { label: 'High Overtaking',       color: '#0284c7', bg: 'rgba(2,132,199,0.08)',  border: 'rgba(2,132,199,0.2)' },
  MEDIUM:      { label: 'Medium Overtaking',     color: '#d97706', bg: 'rgba(217,119,6,0.08)',  border: 'rgba(217,119,6,0.2)' },
  LOW:         { label: 'Low Overtaking',        color: '#ea580c', bg: 'rgba(234,88,12,0.08)',  border: 'rgba(234,88,12,0.2)' },
  'VERY LOW':  { label: 'Very Low Overtaking',   color: '#dc2626', bg: 'rgba(220,38,38,0.08)',  border: 'rgba(220,38,38,0.2)' },
}
