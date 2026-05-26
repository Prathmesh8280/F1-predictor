import fastf1
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

from src.data_loader import load_history, load_qualifying, load_practice_pace
from src.features import (
    build_circuit_map,
    build_circuit_features,
    build_stage2_training_data,
    build_prediction_features,
    STAGE1_FEATURES,
    STAGE2_FEATURES,
)
from src import model as mdl


def run(race: str, year: int, train_years=(2024, 2025), force_refresh=False):
    """Two-stage F1 prediction pipeline.

    Stage 1 — Circuit baseline (2024-2025):
        Ridge regression on grid_position + circuit identity.
        Learns "at Monaco, P1 qualifiers finish P1 most of the time" style
        patterns that are stable across regulation changes.

    Stage 2 — Current pace (2026 only):
        Ridge regression on qualifying gap to pole, FP2/sprint long-run pace,
        and driver/team form from races completed so far this season.
        Captures who is actually fast under the new regulations.

    Final prediction = 35% Stage 1  +  65% Stage 2.
    """
    # Years to use for circuit pattern training (exclude the current prediction year)
    circuit_years = tuple(y for y in train_years if y != year)
    if not circuit_years:
        circuit_years = train_years

    # ── Stage 1: circuit baseline ────────────────────────────────────────────
    print(f"\n[Stage 1] Loading circuit pattern data for {list(circuit_years)}...")
    history_circuit = load_history(train_years=circuit_years, force_refresh=force_refresh)

    circuit_map = build_circuit_map(history_circuit)
    x1_train, y1_train, circuit_map = build_circuit_features(history_circuit, circuit_map)

    print("[Stage 1] Training circuit baseline model...")
    stage1_model = mdl.train_stage1(x1_train, y1_train)

    # ── Stage 2: current-season pace ─────────────────────────────────────────
    print(f"\n[Stage 2] Loading {year} race data...")
    history_2026 = load_history(train_years=(year,), force_refresh=force_refresh)

    # Identify the target race round so we can exclude it from training
    try:
        target_event = fastf1.get_event(year, race)
        target_round = int(target_event["RoundNumber"])
    except Exception:
        target_round = -1

    history_2026_train = history_2026[history_2026["round"] != target_round]
    rounds_2026 = sorted(history_2026_train["round"].unique())

    quali_by_round: dict = {}
    practice_by_round: dict = {}

    for r in rounds_2026:
        event_name = history_2026_train[history_2026_train["round"] == r]["event_name"].iloc[0]
        try:
            quali_by_round[r] = load_qualifying(year, r)
        except Exception as e:
            print(f"  Skipping qualifying R{r} ({event_name}): {e}")
        try:
            practice_by_round[r] = load_practice_pace(year, r)
        except Exception as e:
            print(f"  Skipping practice R{r} ({event_name}): {e}")

    stage2_df = build_stage2_training_data(history_2026_train, practice_by_round, quali_by_round)

    use_stage2 = len(stage2_df) >= 10
    if use_stage2:
        print(f"[Stage 2] Training pace model on {len(stage2_df)} driver-race rows...")
        stage2_model = mdl.train_stage2(
            stage2_df[STAGE2_FEATURES],
            stage2_df["finish_position"].values,
        )
    else:
        print("[Stage 2] Insufficient 2026 data — using Stage 1 (circuit baseline) only.")
        stage2_model = None

    # ── Prediction ───────────────────────────────────────────────────────────
    print(f"\n[Predict] Fetching session data for {year} {race}...")
    quali_df = load_qualifying(year, race)
    if quali_df.empty:
        raise RuntimeError(f"No qualifying data found for {year} {race}")

    practice_pace = load_practice_pace(year, race)

    # Form features must not include the race being predicted
    history_for_form = history_2026[history_2026["round"] != target_round]

    x_circuit, x_pace = build_prediction_features(
        quali_df=quali_df,
        practice_pace=practice_pace,
        history_2026=history_for_form,
        event_name=race,
        circuit_map=circuit_map,
    )

    if use_stage2:
        predicted_positions = mdl.predict_blended(stage1_model, stage2_model, x_circuit, x_pace)
        mae1 = mean_absolute_error(y1_train, stage1_model.predict(x1_train[STAGE1_FEATURES]))
        mae2 = mean_absolute_error(
            stage2_df["finish_position"].values,
            stage2_model.predict(stage2_df[STAGE2_FEATURES]),
        )
        mae = mdl.BLEND_ALPHA * mae1 + (1 - mdl.BLEND_ALPHA) * mae2
    else:
        predicted_positions = stage1_model.predict(x_circuit[STAGE1_FEATURES])
        mae = mean_absolute_error(y1_train, stage1_model.predict(x1_train[STAGE1_FEATURES]))

    results = x_circuit[["driver", "team", "grid_position"]].copy()
    results = results.iloc[np.argsort(predicted_positions)].reset_index(drop=True)
    results["predicted_rank"] = results.index + 1

    return results, mae
