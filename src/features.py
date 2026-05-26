import pandas as pd
import numpy as np

# Feature column lists consumed by model.py pipelines
STAGE1_FEATURES = ["grid_position", "circuit_encoded"]
STAGE2_FEATURES = ["quali_gap_to_pole", "practice_pace_gap", "driver_avg_finish_2026", "team_avg_finish_2026"]


def build_circuit_map(history: pd.DataFrame) -> dict:
    """Map each event name to a stable string category ID."""
    all_circuits = sorted(history["event_name"].unique())
    return {name: str(idx) for idx, name in enumerate(all_circuits)}


def build_circuit_features(history: pd.DataFrame, circuit_map: dict = None):
    """Stage 1 features: grid position + circuit identity.

    Trained on 2024-2025 data. Captures how grid position translates to
    finish position at each specific circuit — no team or driver identity.

    Returns (X, y, circuit_map).
    """
    if circuit_map is None:
        circuit_map = build_circuit_map(history)

    rows = []
    for _, row in history.iterrows():
        rows.append({
            "grid_position": float(row["grid_position"]),
            "circuit_encoded": circuit_map.get(row["event_name"], "unknown"),
            "finish_position": float(row["finish_position"]),
        })

    df = pd.DataFrame(rows)
    X = df[STAGE1_FEATURES]
    y = df["finish_position"].values
    return X, y, circuit_map


def build_stage2_training_data(
    history_2026: pd.DataFrame,
    practice_paces: dict,
    quali_data: dict,
) -> pd.DataFrame:
    """Build pace feature rows for Stage 2 training from completed 2026 races.

    practice_paces : {round_num: DataFrame(driver, practice_pace_s)}
    quali_data     : {round_num: DataFrame(driver, qualifying_time_s, grid_position)}

    For each race, form features use only the races that came BEFORE it so
    there is no data leakage.
    """
    rows = []
    rounds = sorted(history_2026["round"].unique())

    for round_num in rounds:
        race_results = history_2026[history_2026["round"] == round_num]
        quali = quali_data.get(round_num)
        if quali is None or quali.empty:
            continue

        pole_time = quali["qualifying_time_s"].min()
        practice = practice_paces.get(round_num)
        fastest_practice = (
            practice["practice_pace_s"].min()
            if practice is not None and not practice.empty
            else None
        )

        # Form is computed from races strictly before this round
        prev_races = history_2026[history_2026["round"] < round_num]

        for _, result in race_results.iterrows():
            driver = result["driver"]
            team = result["team"]

            driver_quali = quali[quali["driver"] == driver]
            if driver_quali.empty:
                continue

            q_time = driver_quali["qualifying_time_s"].iloc[0]
            quali_gap = (
                float(q_time - pole_time)
                if q_time is not None and not pd.isna(q_time) and pole_time is not None
                else np.nan
            )

            practice_gap = np.nan
            if practice is not None and not practice.empty and fastest_practice is not None:
                driver_practice = practice[practice["driver"] == driver]
                if not driver_practice.empty:
                    practice_gap = float(driver_practice["practice_pace_s"].iloc[0] - fastest_practice)

            driver_prev = prev_races[prev_races["driver"] == driver]
            driver_avg = driver_prev["finish_position"].mean() if not driver_prev.empty else np.nan

            team_prev = prev_races[prev_races["team"] == team]
            team_avg = team_prev["finish_position"].mean() if not team_prev.empty else np.nan

            rows.append({
                "quali_gap_to_pole": quali_gap,
                "practice_pace_gap": practice_gap,
                "driver_avg_finish_2026": driver_avg,
                "team_avg_finish_2026": team_avg,
                "finish_position": float(result["finish_position"]),
            })

    return pd.DataFrame(rows)


def build_prediction_features(
    quali_df: pd.DataFrame,
    practice_pace: pd.DataFrame,
    history_2026: pd.DataFrame,
    event_name: str,
    circuit_map: dict,
) -> tuple:
    """Build (X_circuit, X_pace) DataFrames for predicting a specific race.

    history_2026 should already exclude the target race so form features
    are not contaminated by the race being predicted.
    """
    circuit_id = _fuzzy_match_circuit(event_name, circuit_map)

    pole_time = quali_df["qualifying_time_s"].min()
    fastest_practice = (
        practice_pace["practice_pace_s"].min()
        if practice_pace is not None and not practice_pace.empty
        else None
    )

    circuit_rows, pace_rows = [], []

    for _, driver_row in quali_df.iterrows():
        driver = driver_row["driver"]
        team = driver_row["team"]
        grid = float(driver_row["grid_position"])

        circuit_rows.append({
            "driver": driver,
            "team": team,
            "grid_position": grid,
            "circuit_encoded": circuit_id,
        })

        q_time = driver_row.get("qualifying_time_s")
        quali_gap = (
            float(q_time - pole_time)
            if q_time is not None and not pd.isna(q_time) and pole_time is not None
            else np.nan
        )

        practice_gap = np.nan
        if practice_pace is not None and not practice_pace.empty and fastest_practice is not None:
            driver_practice = practice_pace[practice_pace["driver"] == driver]
            if not driver_practice.empty:
                practice_gap = float(driver_practice["practice_pace_s"].iloc[0] - fastest_practice)

        driver_hist = history_2026[history_2026["driver"] == driver]
        driver_avg = driver_hist["finish_position"].mean() if not driver_hist.empty else np.nan

        team_hist = history_2026[history_2026["team"] == team]
        team_avg = team_hist["finish_position"].mean() if not team_hist.empty else np.nan

        pace_rows.append({
            "driver": driver,
            "team": team,
            "quali_gap_to_pole": quali_gap,
            "practice_pace_gap": practice_gap,
            "driver_avg_finish_2026": driver_avg,
            "team_avg_finish_2026": team_avg,
        })

    return pd.DataFrame(circuit_rows), pd.DataFrame(pace_rows)


def _fuzzy_match_circuit(event_name: str, circuit_map: dict) -> str:
    """Match a user-supplied race name to the closest key in circuit_map."""
    if event_name in circuit_map:
        return circuit_map[event_name]

    event_lower = event_name.lower()
    for key, idx in circuit_map.items():
        if event_lower in key.lower() or key.lower() in event_lower:
            print(f"  Circuit match: '{event_name}' -> '{key}'")
            return idx

    print(f"  Warning: circuit '{event_name}' not in training data. Predictions will use grid only.")
    return "unknown"
