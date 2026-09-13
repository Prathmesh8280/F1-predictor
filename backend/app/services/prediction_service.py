"""Prediction application logic.

Calls the ML pipeline (ml.predictor.run), enriches with actual results when the
race is complete, and shapes the response the frontend expects. Results are
cached in-process per (race, year); force_refresh bypasses and refreshes it.
"""
import pandas as pd

import ml.data_loader as dl
from ml.predictor import run

from backend.app.constants import CIRCUIT_META, CIRCUIT_SVG

# In-memory prediction cache: (race, year) → full response dict.
# Bypassed when force_refresh=True; the entry is overwritten on refresh so a
# manual refresh always re-runs the pipeline and updates the cache.
_pred_cache: dict[tuple, dict] = {}


def _int(val):
    return int(val) if val is not None and pd.notna(val) else None


def _flt(val, n=2):
    return round(float(val), n) if val is not None and pd.notna(val) else None


def generate_prediction(race: str, year: int, force_refresh: bool = False) -> dict:
    """Run (or serve cached) the prediction pipeline for a race.

    Raises RuntimeError if the race/data is unavailable (→ 404 at the route).
    """
    cache_key = (race, year)

    # Only serve from cache if the race was already completed when cached.
    # Incomplete predictions are never cached so a re-request always re-checks
    # FastF1 for actual results without needing an explicit force_refresh.
    if not force_refresh and cache_key in _pred_cache and _pred_cache[cache_key]["is_completed"]:
        return _pred_cache[cache_key]

    results, backtest = run(race=race, year=year, force_refresh=force_refresh)

    actual_df = dl.load_actual_results(year, race)
    is_completed = actual_df is not None and not actual_df.empty

    actual_map: dict = {}
    if is_completed:
        actual_map = dict(zip(actual_df["driver"], actual_df["actual_position"].astype(int)))

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

    circuit_key = race
    meta = CIRCUIT_META.get(circuit_key, {"country_code": "un", "name": circuit_key, "overtaking": "MEDIUM"})

    response = {
        "race": race,
        "year": year,
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
