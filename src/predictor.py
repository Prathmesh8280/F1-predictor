import json
import os

import fastf1
import numpy as np
import pandas as pd

from src.data_loader import load_history, load_qualifying, load_practice_pace, normalise_location, fetch_race_grid
from src.features import (
    build_circuit_map,
    build_circuit_features,
    build_stage2_training_data,
    build_prediction_features,
    STAGE1_FEATURES,
)
from src import model as mdl

MIN_STAGE2_ROWS = 15

_BACKTEST_SUMMARY = os.path.join(os.path.dirname(__file__), "..", "data", "backtest_summary.json")

_RACE_ALIASES = {
    "cota": "Austin",
    "vegas": "Las Vegas",
    "interlagos": "Sao Paulo",
    "spa": "Belgium",
    "imola": "Emilia Romagna",
    "silverstone": "Britain",
    "zandvoort": "Netherlands",
}


def resolve_event(year: int, race: str):
    """Resolve a user-supplied race name to a FastF1 event."""
    key = _RACE_ALIASES.get(race.strip().lower(), race)
    try:
        return fastf1.get_event(year, key)
    except Exception:
        return None


# Standard F1 points for finishing position
_F1_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

# ── Reusable model seams (shared by the live predictor and the backtest) ──────

def compute_championship_standings(season_history: pd.DataFrame) -> tuple:
    """Compute driver and constructor standings from completed rounds this season.

    season_history: race results for rounds already completed (before the target race).
    Returns (driver_standings, constructor_standings) DataFrames.
    driver_standings    — columns: driver, driver_points
    constructor_standings — columns: team, constructor_points
    Empty DataFrames returned for round 1 (no completed races yet).
    """
    empty_d = pd.DataFrame(columns=["driver", "driver_points"])
    empty_c = pd.DataFrame(columns=["team", "constructor_points"])
    if season_history is None or season_history.empty:
        return empty_d, empty_c

    hist = season_history.copy()
    hist["points"] = hist["finish_position"].map(_F1_POINTS).fillna(0)

    driver_standings = (
        hist.groupby("driver")["points"]
        .sum()
        .reset_index()
        .rename(columns={"points": "driver_points"})
    )
    constructor_standings = (
        hist.groupby("team")["points"]
        .sum()
        .reset_index()
        .rename(columns={"points": "constructor_points"})
    )
    return driver_standings, constructor_standings



def build_circuit_model(history_circuit: pd.DataFrame, circuit_map: dict = None,
                        verbose: bool = True, only_location: str = None):
    """Fit Stage 1 — circuit delta baseline — on historical race results.

    Stage 1 now predicts position DELTA (finish − grid) rather than absolute
    finish position. Ridge learns circuit-specific delta patterns (e.g. at
    Monaco all deltas ≈ 0; at Bahrain midfield slots tend to gain). Falls back
    to the global cross-circuit slope for circuits not in training data.

    Returns (stage1_model, circuit_map).
    """
    if only_location is not None:
        subset = history_circuit[history_circuit["location"] == only_location]
        if len(subset) >= 15:
            history_circuit, circuit_map = subset, None
    if circuit_map is None:
        circuit_map = build_circuit_map(history_circuit)
    x1_train, y1_delta, circuit_map = build_circuit_features(history_circuit, circuit_map)
    stage1_model = mdl.train_stage1(x1_train, y1_delta, verbose=verbose)
    return stage1_model, circuit_map


def build_pace_model(
    season_history: pd.DataFrame,
    practice_by_round: dict,
    quali_by_round: dict,
    verbose: bool = True,
    features=None,
    estimator=None,
):
    """Fit Stage 2 Ridge on current-season race results.

    Features: championship_rank, constructor_rank, fp2_pace_rank (all 1..N).
    Target: position_delta = finish − grid (no leakage — standings computed
    from rounds strictly before each training race).

    Returns (stage2_model, stage2_df); model is None when fewer than
    MIN_STAGE2_ROWS training rows are available (i.e. Round 1 only).
    """
    stage2_df = build_stage2_training_data(
        season_history, practice_by_round, quali_by_round
    )
    if len(stage2_df) < MIN_STAGE2_ROWS:
        return None, stage2_df
    stage2_model = mdl.train_stage2(
        stage2_df,
        stage2_df["position_delta"].values,
        features=features,
        estimator=estimator,
        verbose=verbose,
    )
    return stage2_model, stage2_df


def predict_components(
    stage1_model,
    circuit_map: dict,
    quali_df: pd.DataFrame,
    practice_pace: pd.DataFrame,
    history_for_form: pd.DataFrame,
    circuit_location: str,
):
    """Raw, un-blended predictions for a single race.

    Returns (x_circuit, delta1, stage2_rank) where:
      delta1      — Stage 1 position delta per driver (finish − grid).
      stage2_rank — Stage 2 composite rank (1..N, lower = better), or None
                    when no FP2 data and no prior standings exist (Round 1).

    Stage 2 is a manual weighted rank blend of three signals:
      championship_rank  (35%) — driver points accumulated this season
      constructor_rank   (35%) — team points accumulated this season
      fp2_pace_rank      (30%) — this weekend's FP2 / Sprint long-run pace

    Weights auto-normalise when any signal is missing (e.g. Round 1 has no
    standings yet so only FP2 pace contributes).

    NOTE: A trained Ridge alternative exists in build_pace_model(). It requires
    a full prior season of data (~440 rows) to outperform these calibrated
    weights — activate it when predicting into a new season using the previous
    season as training data.
    """
    driver_standings, constructor_standings = compute_championship_standings(history_for_form)

    x_circuit, _ = build_prediction_features(
        quali_df=quali_df,
        practice_pace=practice_pace,
        circuit_location=circuit_location,
        circuit_map=circuit_map,
        driver_standings=driver_standings,
        constructor_standings=constructor_standings,
    )

    delta1 = stage1_model.predict(x_circuit[STAGE1_FEATURES])

    drivers = x_circuit["driver"]

    def _rank_col(df, col, key_col="driver", ascending=True):
        lookup = df.set_index(key_col)[col]
        vals = drivers.map(lookup)
        fill_val = vals.max() if ascending and vals.notna().any() else 0.0
        return vals.fillna(fill_val).rank(ascending=ascending, method="min").values

    signals, weights = [], []

    if not driver_standings.empty:
        signals.append(_rank_col(driver_standings, "driver_points", ascending=False))
        weights.append(mdl.DRIVER_CHAMP_WEIGHT)

    if not constructor_standings.empty and "team" in quali_df.columns:
        team_map = quali_df[["driver", "team"]].drop_duplicates().set_index("driver")["team"]
        driver_constructor = pd.DataFrame({"driver": drivers})
        driver_constructor["team"] = driver_constructor["driver"].map(team_map)
        driver_constructor = driver_constructor.merge(constructor_standings, on="team", how="left")
        driver_constructor["constructor_points"] = driver_constructor["constructor_points"].fillna(0)
        signals.append(driver_constructor["constructor_points"].rank(ascending=False, method="min").values)
        weights.append(mdl.CONSTRUCTOR_CHAMP_WEIGHT)

    has_fp2 = (
        practice_pace is not None
        and not practice_pace.empty
        and "practice_pace_s" in practice_pace.columns
        and practice_pace["practice_pace_s"].notna().any()
    )
    if has_fp2:
        signals.append(_rank_col(practice_pace, "practice_pace_s", ascending=True))
        weights.append(mdl.FP2_WEIGHT)

    stage2_rank = None
    if signals:
        total_w = sum(weights)
        stage2_rank = sum(s * w / total_w for s, w in zip(signals, weights))

    return x_circuit, delta1, stage2_rank


def predict_one(
    stage1_model,
    circuit_map: dict,
    quali_df: pd.DataFrame,
    practice_pace: pd.DataFrame,
    history_for_form: pd.DataFrame,
    circuit_location: str,
    alpha: float = None,
) -> pd.DataFrame:
    """Predict the finishing order for a single race.

    Stage 1 circuit-adjusts the grid: circuit_rank = rank(grid + delta1).
    Stage 2 ranks drivers by: championship points form + constructor points form + FP2 pace.
    Final blend: score = alpha * circuit_rank + (1 - alpha) * stage2_rank
    alpha=1 → pure Stage 1 (circuit-adjusted grid); alpha=0 → pure Stage 2 (form + pace).
    """
    x_circuit, delta1, stage2_rank = predict_components(
        stage1_model, circuit_map,
        quali_df, practice_pace, history_for_form, circuit_location,
    )

    grid = x_circuit["grid_position"].values
    a = mdl.BLEND_ALPHA if alpha is None else alpha

    # Stage 1: circuit-adjusted grid rank
    circuit_adjusted = grid + delta1
    circuit_rank = pd.Series(circuit_adjusted).rank(method="min").values

    if stage2_rank is not None:
        score = a * circuit_rank + (1 - a) * stage2_rank
    else:
        score = circuit_rank

    predicted_positions = score

    results = x_circuit[["driver", "team", "grid_position"]].copy()
    results = results.iloc[np.argsort(predicted_positions)].reset_index(drop=True)
    results["predicted_rank"] = results.index + 1
    return results


def latest_backtest_stats():
    """Out-of-sample stats from the most recent backtest, or empty dict."""
    if not os.path.exists(_BACKTEST_SUMMARY):
        return {}
    try:
        with open(_BACKTEST_SUMMARY) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _load_round_sessions(year: int, rounds, history_train: pd.DataFrame, force_refresh: bool = False):
    """Fetch qualifying and FP2 practice pace for each prior round this season."""
    quali_by_round: dict = {}
    practice_by_round: dict = {}
    for r in rounds:
        event_name = history_train[history_train["round"] == r]["event_name"].iloc[0]
        try:
            quali_by_round[r] = load_qualifying(year, r, force_refresh=force_refresh)
        except Exception as e:
            print(f"  Skipping qualifying R{r} ({event_name}): {e}")
        try:
            practice_by_round[r] = load_practice_pace(year, r, force_refresh=force_refresh)
        except Exception as e:
            print(f"  Skipping FP2 R{r} ({event_name}): {e}")
    return quali_by_round, practice_by_round


def run(race: str, year: int, train_years=(2024, 2025), force_refresh=False):
    """Two-stage F1 prediction pipeline.

    Stage 1 — Circuit baseline (historical seasons):
        Ridge on grid_position + circuit identity, target = finish − grid.
        Learns circuit-specific tendencies (Monaco grid stays, Bahrain midfield gains).

    Stage 2 — Trained Ridge on current-season results (from Round 2 onward):
        Features: championship_rank, constructor_rank, fp2_pace_rank (all 1..N, lower = better).
        Target: position_delta = finish − grid. Trained walk-forward on all prior rounds.
        Falls back to manual weighted rank blend for Round 1 (no prior data).
        FP2 falls back to teammate pace when a driver's laps are all marked inaccurate.

    Final blend: score = alpha * circuit_rank + (1 - alpha) * stage2_rank.
    alpha=0.60 tuned on Spearman rank correlation (0.806 vs grid baseline 0.640, 31 OOS races).
    """
    circuit_years = tuple(y for y in train_years if y != year)
    if not circuit_years:
        circuit_years = train_years

    target_event = resolve_event(year, race)
    if target_event is not None:
        target_round    = int(target_event["RoundNumber"])
        target_location = normalise_location(target_event.get("Location", race))
    else:
        target_round    = -1
        target_location = normalise_location(race)

    # ── Stage 1: circuit delta baseline ──────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  F1 Predictor: {year} {race} Grand Prix")
    print(f"  Training on seasons: {list(circuit_years)}")
    print(f"{'='*55}\n")

    print(f"[Stage 1] Loading circuit pattern data for {list(circuit_years)}...")
    history_circuit = load_history(train_years=circuit_years, force_refresh=force_refresh)

    print(f"[Stage 1] Training circuit delta baseline for '{target_location}'...")
    stage1_model, circuit_map = build_circuit_model(
        history_circuit, only_location=target_location
    )

    # ── Stage 2: championship form + FP2 pace ────────────────────────────────
    print(f"\n[Stage 2] Loading {year} season data (rounds before {race})...")
    history_season       = load_history(train_years=(year,), force_refresh=force_refresh)
    history_season_train = history_season[history_season["round"] < target_round]
    rounds_season        = sorted(history_season_train["round"].unique())

    quali_by_round, practice_by_round = _load_round_sessions(
        year, rounds_season, history_season_train, force_refresh=force_refresh
    )

    n_rounds = len(rounds_season)
    if n_rounds > 0:
        print(f"[Stage 2] {n_rounds} prior round(s) loaded — using championship standings + FP2 pace.")
    else:
        print("[Stage 2] Round 1 — no prior standings, FP2 pace only.")

    # ── Prediction ───────────────────────────────────────────────────────────
    print(f"\n[Predict] Fetching session data for {year} {race}...")
    quali_df = load_qualifying(year, race, force_refresh=force_refresh)
    if quali_df.empty:
        raise RuntimeError(f"No qualifying data found for {year} {race}")

    # Overlay the actual starting grid (includes post-qualifying penalties).
    # Two sources, in priority order:
    #   1. history_season — available once the race has finished; grid_position
    #      there comes from the race session so penalties are already applied.
    #   2. fetch_race_grid — live FastF1 call used when the race is in progress
    #      or qualifying penalties have been published but the race hasn't started.
    #      Falls back silently to qualifying order if the session isn't up yet.
    race_rows = history_season[history_season["round"] == target_round]
    if not race_rows.empty:
        grid_map = race_rows.set_index("driver")["grid_position"].to_dict()
    else:
        grid_map = fetch_race_grid(year, race)

    if grid_map:
        quali_df = quali_df.copy()
        quali_df["grid_position"] = (
            quali_df["driver"].map(grid_map).fillna(quali_df["grid_position"]).astype(int)
        )

    practice_pace    = load_practice_pace(year, race, force_refresh=force_refresh)
    history_for_form = history_season[history_season["round"] < target_round]

    results = predict_one(
        stage1_model=stage1_model,
        circuit_map=circuit_map,
        quali_df=quali_df,
        practice_pace=practice_pace,
        history_for_form=history_for_form,
        circuit_location=target_location,
    )

    return results, latest_backtest_stats()
