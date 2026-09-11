import pandas as pd
import numpy as np

# Feature column lists consumed by model.py pipelines
STAGE1_FEATURES = ["grid_position", "circuit_encoded"]

# F1 points system used to compute championship standings features
_F1_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

# Stage 2 uses three rank features (all 1..N, lower = better).
# Ranks rather than raw values so the model generalises across different
# points totals at different stages of the season.
STAGE2_FEATURES = [
    "championship_rank",  # 1 = championship leader, N = last in standings
    "constructor_rank",   # 1 = leading constructor, N = last
    "fp2_pace_rank",      # 1 = fastest FP2/Sprint long-run pace, N = slowest
]


def build_circuit_map(history: pd.DataFrame) -> dict:
    """Map each circuit location to a stable string category ID."""
    all_circuits = sorted(history["location"].unique())
    return {name: str(idx) for idx, name in enumerate(all_circuits)}



def build_circuit_features(history: pd.DataFrame, circuit_map: dict = None):
    """Stage 1 features: grid position + circuit identity.

    Target is now position DELTA (finish − grid), not absolute finish position.
    Ridge learns circuit-specific delta patterns: at Monaco deltas ≈ 0 for all
    grid slots; at Bahrain the midfield tends to gain; etc. The GridCircuit-
    Interaction step gives each circuit its own delta slope so the regularised
    global pattern can be overridden per track when enough data exists.

    Returns (X, y_delta, circuit_map).
    """
    if circuit_map is None:
        circuit_map = build_circuit_map(history)

    rows = []
    for _, row in history.iterrows():
        rows.append({
            "grid_position": float(row["grid_position"]),
            "circuit_encoded": circuit_map.get(row["location"], "unknown"),
            "delta": float(row["finish_position"]) - float(row["grid_position"]),
        })

    df = pd.DataFrame(rows)
    X = df[STAGE1_FEATURES]
    y = df["delta"].values
    return X, y, circuit_map


def build_stage2_training_data(
    history_2026: pd.DataFrame,
    practice_paces: dict,
    quali_data: dict,
) -> pd.DataFrame:
    """Build Stage 2 training rows from completed current-season races.

    Three rank features (all 1..N, lower = better):
      championship_rank  — driver's standing by points before this round
      constructor_rank   — team's standing by points before this round
      fp2_pace_rank      — FP2/Sprint long-run pace rank for this round

    Ranks rather than raw values so Ridge generalises across the full range
    of points totals seen at different stages of the season.

    Target: position_delta = finish − grid. No leakage — standings and form
    are computed strictly from rounds before each training race.
    """
    rows = []
    rounds = sorted(history_2026["round"].unique())

    for round_num in rounds:
        race_results = history_2026[history_2026["round"] == round_num]
        if race_results.empty:
            continue

        prev_races = history_2026[history_2026["round"] < round_num]

        # Championship ranks before this round (1 = most points)
        if not prev_races.empty:
            prev = prev_races.copy()
            prev["_pts"] = prev["finish_position"].map(_F1_POINTS).fillna(0)
            driver_pts  = prev.groupby("driver")["_pts"].sum().sort_values(ascending=False)
            team_pts    = prev.groupby("team")["_pts"].sum().sort_values(ascending=False)
            driver_rank_map = {drv: i + 1 for i, drv in enumerate(driver_pts.index)}
            team_rank_map   = {team: i + 1 for i, team in enumerate(team_pts.index)}
        else:
            driver_rank_map, team_rank_map = {}, {}

        # FP2 pace ranks for this round (1 = fastest)
        practice = practice_paces.get(round_num)
        fp2_rank_map: dict = {}
        if practice is not None and not practice.empty and "practice_pace_s" in practice.columns:
            sorted_fp2 = practice.dropna(subset=["practice_pace_s"]).sort_values("practice_pace_s")
            fp2_rank_map = {row["driver"]: i + 1 for i, (_, row) in enumerate(sorted_fp2.iterrows())}

        n_drivers = len(race_results)
        n_teams   = max(len(race_results["team"].unique()), 1)

        for _, result in race_results.iterrows():
            driver = result["driver"]
            team   = result["team"]
            grid   = float(result["grid_position"])

            rows.append({
                "championship_rank": float(driver_rank_map.get(driver, n_drivers)),
                "constructor_rank":  float(team_rank_map.get(team, n_teams)),
                "fp2_pace_rank":     float(fp2_rank_map.get(driver, n_drivers)),
                "position_delta":    float(result["finish_position"]) - grid,
            })

    return pd.DataFrame(rows)


def build_prediction_features(
    quali_df: pd.DataFrame,
    practice_pace: pd.DataFrame,
    circuit_location: str,
    circuit_map: dict,
    driver_standings: pd.DataFrame = None,
    constructor_standings: pd.DataFrame = None,
) -> tuple:
    """Build (X_circuit, X_pace) DataFrames for predicting a specific race.

    X_circuit: Stage 1 features (grid_position, circuit_encoded) + driver/team meta.
    X_pace:    Stage 2 features matching STAGE2_FEATURES — three rank columns
               (championship_rank, constructor_rank, fp2_pace_rank), all 1..N,
               lower = better, so the Ridge sign convention is consistent with
               training data from build_stage2_training_data().
    """
    circuit_id = circuit_map.get(circuit_location, "unknown")
    if circuit_id == "unknown":
        print(f"  Warning: circuit '{circuit_location}' not in training data — Stage 1 uses global slope.")

    n_drivers = len(quali_df)
    n_teams   = max(len(quali_df["team"].unique()), 1) if "team" in quali_df.columns else n_drivers

    # Championship ranks (1 = leader, N = last in standings)
    driver_rank_map: dict = {}
    if driver_standings is not None and not driver_standings.empty:
        sorted_d = driver_standings.sort_values("driver_points", ascending=False)
        driver_rank_map = {row["driver"]: i + 1 for i, (_, row) in enumerate(sorted_d.iterrows())}

    team_rank_map: dict = {}
    if constructor_standings is not None and not constructor_standings.empty:
        sorted_c = constructor_standings.sort_values("constructor_points", ascending=False)
        team_rank_map = {row["team"]: i + 1 for i, (_, row) in enumerate(sorted_c.iterrows())}

    # FP2 pace ranks (1 = fastest long-run pace)
    fp2_rank_map: dict = {}
    if practice_pace is not None and not practice_pace.empty and "practice_pace_s" in practice_pace.columns:
        sorted_fp2 = practice_pace.dropna(subset=["practice_pace_s"]).sort_values("practice_pace_s")
        fp2_rank_map = {row["driver"]: i + 1 for i, (_, row) in enumerate(sorted_fp2.iterrows())}

    circuit_rows: list = []
    pace_rows: list = []

    for _, driver_row in quali_df.iterrows():
        driver = driver_row["driver"]
        team   = driver_row.get("team", "")
        grid   = float(driver_row["grid_position"])

        circuit_rows.append({
            "driver":          driver,
            "team":            team,
            "grid_position":   grid,
            "circuit_encoded": circuit_id,
        })

        pace_rows.append({
            "driver":              driver,
            "team":                team,
            "championship_rank":   float(driver_rank_map.get(driver, n_drivers)),
            "constructor_rank":    float(team_rank_map.get(team, n_teams)),
            "fp2_pace_rank":       float(fp2_rank_map.get(driver, n_drivers)),
        })

    return pd.DataFrame(circuit_rows), pd.DataFrame(pace_rows)
