import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import fastf1
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

import src.data_loader as dl
from src.predictor import run, latest_backtest_stats

fastf1.Cache.enable_cache(str(dl.CACHE_DIR))

LOGOS_DIR = os.path.join(dl.CACHE_DIR, "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

# Maps frontend slug → (year, f1_cdn_slug)
_LOGO_SLUGS: dict[str, tuple[str, str]] = {
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

app = FastAPI(title="F1 Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    race: str
    year: int
    force_refresh: bool = False


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
_ROUND_MAP: dict[int, dict[int, str]] = {
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
_FF1_TO_KEY: dict[str, str] = {
    "Great Britain": "Britain",
    "United Kingdom": "Britain",
    "Mexico": "Mexico City",
    "Brasil": "Brazil",
    "UAE": "Abu Dhabi",
    "United Arab Emirates": "Abu Dhabi",
}

# Fallback keyword overrides for multi-race countries
_EVENTNAME_KEYWORD: list[tuple[str, str]] = [
    ("miami",             "Miami"),
    ("las vegas",         "Las Vegas"),
    ("united states",     "United States"),
    ("spanish grand prix","Madrid"),
    ("emilia",            "Italy"),
]


def _ff1_to_race_key(country: str, event_name: str, year: int = 0, round_num: int = 0) -> str | None:
    # Primary: round-number map is unambiguous
    if year and round_num:
        key = _ROUND_MAP.get(year, {}).get(round_num)
        if key:
            return key
    # Fallback: keyword matching then country mapping
    en = event_name.lower()
    for keyword, key in _EVENTNAME_KEYWORD:
        if keyword in en:
            return key
    mapped = _FF1_TO_KEY.get(country, country)
    return mapped if mapped in CIRCUIT_META else None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/logo/{slug}")
def get_logo(slug: str):
    entry = _LOGO_SLUGS.get(slug.lower())
    if not entry:
        raise HTTPException(status_code=404, detail="Unknown team slug")

    year, f1slug = entry
    cached_path = os.path.join(LOGOS_DIR, f"{f1slug}.webp")

    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 100:
        with open(cached_path, "rb") as f:
            return Response(
                content=f.read(),
                media_type="image/webp",
                headers={"Cache-Control": "public, max-age=86400"},
            )

    url = (
        f"https://media.formula1.com/image/upload/f_auto/q_auto/v1"
        f"/common/f1/{year}/{f1slug}/{year}{f1slug}logo.webp"
    )
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "image/webp,image/*,*/*",
            "Referer": "https://www.formula1.com/",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        if len(data) > 100:
            with open(cached_path, "wb") as f:
                f.write(data)
            return Response(
                content=data,
                media_type="image/webp",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch logo: {e}")

    raise HTTPException(status_code=404, detail="Logo unavailable")


@app.get("/races")
def get_races(year: int = 2026):
    from datetime import date, timedelta

    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load schedule: {e}")

    today = date.today()
    cutoff = today + timedelta(days=4)  # include up to ~end of current race weekend

    races = []
    for _, ev in schedule.iterrows():
        event_date = ev["EventDate"]
        if hasattr(event_date, "date"):
            event_date = event_date.date()
        if event_date > cutoff:
            continue

        country = str(ev.get("Country", ""))
        event_name = str(ev.get("EventName", ""))
        round_num = int(ev["RoundNumber"])
        key = _ff1_to_race_key(country, event_name, year=year, round_num=round_num)
        if key is None:
            continue

        status = "completed" if event_date < today else "current"
        races.append({
            "name": key,
            "round": round_num,
            "date": str(event_date),
            "status": status,
        })

    return sorted(races, key=lambda r: r["round"])


# In-memory prediction cache: (race, year) → full response dict.
# Bypassed when force_refresh=True. Cleared entry-by-entry on force_refresh
# so a manual refresh always re-runs the pipeline and updates the cache.
_pred_cache: dict[tuple, dict] = {}


@app.post("/predict")
def predict(req: PredictRequest):
    cache_key = (req.race, req.year)

    if not req.force_refresh and cache_key in _pred_cache:
        return _pred_cache[cache_key]

    try:
        results, backtest = run(
            race=req.race,
            year=req.year,
            force_refresh=req.force_refresh,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    actual_df = dl.load_actual_results(req.year, req.race)
    is_completed = actual_df is not None and not actual_df.empty

    actual_map: dict = {}
    if is_completed:
        actual_map = dict(zip(actual_df["driver"], actual_df["actual_position"].astype(int)))

    def _int(val):
        return int(val) if val is not None and pd.notna(val) else None

    def _flt(val, n=2):
        return round(float(val), n) if val is not None and pd.notna(val) else None

    predictions = []
    for _, row in results.iterrows():
        predictions.append({
            "rank":             int(row["predicted_rank"]),
            "driver":           str(row["driver"]),
            "team":             str(row["team"]),
            "grid_pos":         int(row["grid_position"]),
            "actual_rank":      actual_map.get(str(row["driver"])),
            "championship_rank": _int(row.get("championship_rank")),
            "constructor_rank":  _int(row.get("constructor_rank")),
            "fp2_pace_rank":     _int(row.get("fp2_pace_rank")),
            "delta1":            _flt(row.get("delta1")),
            "stage2_used":       bool(row.get("stage2_used", False)),
        })

    circuit_key = req.race
    meta = CIRCUIT_META.get(circuit_key, {"country_code": "un", "name": circuit_key, "overtaking": "MEDIUM"})

    response = {
        "race": req.race,
        "year": req.year,
        "circuit": {
            "name": meta["name"],
            "country_code": meta["country_code"],
            "overtaking": meta["overtaking"],
            "track_img_url": CIRCUIT_SVG.get(circuit_key, ""),
        },
        "predictions": sorted(predictions, key=lambda p: p["rank"]),
        "is_completed": is_completed,
        "model_mae": backtest.get("model_mae_fin"),
        "baseline_mae": backtest.get("baseline_mae_fin"),
    }
    _pred_cache[cache_key] = response
    return response
