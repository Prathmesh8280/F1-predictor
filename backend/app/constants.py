"""Circuit metadata and FastF1 event → circuit-key mapping tables.

These are API-presentation constants (country codes, overtaking ratings,
circuit map URLs, and the round-number map used to resolve FastF1 events to
our canonical circuit keys). They are intentionally kept out of the ML package,
which is concerned only with prediction, not presentation.
"""

CIRCUIT_META: dict[str, dict] = {
    "Australia":     {"country_code": "au", "name": "Albert Park, Melbourne",         "overtaking": "MEDIUM"},
    "China":         {"country_code": "cn", "name": "Shanghai International Circuit",  "overtaking": "HIGH"},
    "Japan":         {"country_code": "jp", "name": "Suzuka Circuit",                  "overtaking": "LOW"},
    "Bahrain":       {"country_code": "bh", "name": "Bahrain International Circuit",   "overtaking": "HIGH"},
    "Saudi Arabia":  {"country_code": "sa", "name": "Jeddah Corniche Circuit",         "overtaking": "MEDIUM"},
    "Miami":         {"country_code": "us", "name": "Miami International Autodrome",   "overtaking": "MEDIUM"},
    "Canada":        {"country_code": "ca", "name": "Circuit Gilles Villeneuve",       "overtaking": "HIGH"},
    "Monaco":        {"country_code": "mc", "name": "Circuit de Monaco",               "overtaking": "VERY LOW"},
    "Spain":         {"country_code": "es", "name": "Circuit de Barcelona-Catalunya",  "overtaking": "LOW"},
    "Austria":       {"country_code": "at", "name": "Red Bull Ring",                   "overtaking": "HIGH"},
    "Britain":       {"country_code": "gb", "name": "Silverstone Circuit",             "overtaking": "HIGH"},
    "Belgium":       {"country_code": "be", "name": "Circuit de Spa-Francorchamps",   "overtaking": "HIGH"},
    "Hungary":       {"country_code": "hu", "name": "Hungaroring",                    "overtaking": "LOW"},
    "Netherlands":   {"country_code": "nl", "name": "Circuit Zandvoort",              "overtaking": "LOW"},
    "Italy":         {"country_code": "it", "name": "Autodromo Nazionale Monza",      "overtaking": "VERY HIGH"},
    "Azerbaijan":    {"country_code": "az", "name": "Baku City Circuit",              "overtaking": "HIGH"},
    "Singapore":     {"country_code": "sg", "name": "Marina Bay Street Circuit",      "overtaking": "VERY LOW"},
    "United States": {"country_code": "us", "name": "Circuit of the Americas",        "overtaking": "MEDIUM"},
    "Mexico City":   {"country_code": "mx", "name": "Autodromo Hermanos Rodriguez",   "overtaking": "MEDIUM"},
    "Brazil":        {"country_code": "br", "name": "Interlagos",                     "overtaking": "HIGH"},
    "Las Vegas":     {"country_code": "us", "name": "Las Vegas Strip Circuit",        "overtaking": "HIGH"},
    "Qatar":         {"country_code": "qa", "name": "Lusail International Circuit",   "overtaking": "MEDIUM"},
    "Abu Dhabi":     {"country_code": "ae", "name": "Yas Marina Circuit",             "overtaking": "MEDIUM"},
    "Madrid":        {"country_code": "es", "name": "Ifema Madrid (Madrid Ring)",      "overtaking": "MEDIUM"},
}

_WP = "https://commons.wikimedia.org/wiki/Special:FilePath/"
CIRCUIT_SVG: dict[str, str] = {
    "Australia":     _WP + "Australia_circuit.svg?width=400",
    "China":         _WP + "Shanghai_international_circuit.svg?width=400",
    "Japan":         _WP + "Suzuka_circuit_map.svg?width=400",
    "Bahrain":       _WP + "Bahrain_International_Circuit--2004.svg?width=400",
    "Saudi Arabia":  _WP + "Jeddah_Street_Circuit.svg?width=400",
    "Miami":         _WP + "Miami_International_Autodrome_track_map.svg?width=400",
    "Canada":        _WP + "Circuit_Gilles_Villeneuve.svg?width=400",
    "Monaco":        _WP + "Monte_Carlo_Formula_1_track_map.svg?width=400",
    "Spain":         _WP + "Circuit_de_barcelona_catalunya.svg?width=400",
    "Austria":       _WP + "Red_Bull_Ring.svg?width=400",
    "Britain":       _WP + "Silverstone_circuit_2011.svg?width=400",
    "Belgium":       _WP + "Spa-Francorchamps_of_Belgium.svg?width=400",
    "Hungary":       _WP + "Hungaroring.svg?width=400",
    "Netherlands":   _WP + "Zandvoort.svg?width=400",
    "Italy":         _WP + "Monza_track_map.svg?width=400",
    "Azerbaijan":    _WP + "Baku_Formula_1_track_map.svg?width=400",
    "Singapore":     _WP + "Singapore_circuit_map.svg?width=400",
    "United States": _WP + "Americas_Formula_1_track_map.svg?width=400",
    "Mexico City":   _WP + "Autodromo_Hermanos_Rodriguez_circuit_map.svg?width=400",
    "Brazil":        _WP + "Interlagos_circuit.svg?width=400",
    "Las Vegas":     _WP + "Las_Vegas_Strip_Circuit_track_map.svg?width=400",
    "Qatar":         _WP + "Losail_International_Circuit_track_map.svg?width=400",
    "Abu Dhabi":     _WP + "Yas_Marina_circuit_2021.svg?width=400",
    "Madrid":        _WP + "Madrid_Ring_circuit_map.svg?width=400",
}

# Round-number → circuit key (primary lookup, year-scoped)
ROUND_MAP: dict[int, dict[int, str]] = {
    2026: {
        1:  "Australia",
        2:  "China",
        3:  "Japan",
        4:  "Miami",
        5:  "Canada",
        6:  "Monaco",
        7:  "Spain",        # Barcelona Grand Prix
        8:  "Austria",
        9:  "Britain",
        10: "Belgium",
        11: "Hungary",
        12: "Netherlands",
        13: "Italy",
        14: "Madrid",       # Spanish Grand Prix (Ifema Madrid Ring)
        15: "Azerbaijan",
        16: "Bahrain",
        17: "Singapore",
        18: "United States",
        19: "Mexico City",
        20: "Brazil",
        21: "Las Vegas",
        22: "Qatar",
        23: "Abu Dhabi",
    },
}

# Fallback: FastF1 country string → our CIRCUIT_META key (for future seasons)
FF1_TO_KEY: dict[str, str] = {
    "Great Britain": "Britain",
    "United Kingdom": "Britain",
    "Mexico": "Mexico City",
    "Brasil": "Brazil",
    "UAE": "Abu Dhabi",
    "United Arab Emirates": "Abu Dhabi",
}

# Fallback keyword overrides for multi-race countries
EVENTNAME_KEYWORD: list[tuple[str, str]] = [
    ("miami",             "Miami"),
    ("las vegas",         "Las Vegas"),
    ("united states",     "United States"),
    ("spanish grand prix", "Madrid"),
    ("emilia",            "Italy"),
]

# Frontend team slug → (year, F1 CDN slug) for logo proxying.
LOGO_SLUGS: dict[str, tuple[str, str]] = {
    "mercedes":     ("2026", "mercedes"),
    "ferrari":      ("2026", "ferrari"),
    "mclaren":      ("2026", "mclaren"),
    "red-bull":     ("2026", "redbullracing"),
    "aston-martin": ("2026", "astonmartin"),
    "alpine":       ("2026", "alpine"),
    "williams":     ("2026", "williams"),
    "haas":         ("2026", "haasf1team"),
    "kick-sauber":  ("2025", "kicksauber"),
    "audi":         ("2026", "audi"),
    "rb":           ("2026", "racingbulls"),
    "cadillac":     ("2026", "cadillac"),
}
