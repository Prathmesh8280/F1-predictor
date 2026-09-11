"""Deterministic tests for feature engineering (no network / FastF1)."""
import pandas as pd

from ml.features import (
    STAGE2_FEATURES,
    build_circuit_features,
    build_circuit_map,
    build_prediction_features,
    build_stage2_training_data,
)


def _history():
    # Two circuits, a few drivers, known grid/finish positions.
    return pd.DataFrame([
        {"round": 1, "location": "Monaco", "driver": "VER", "team": "Red Bull", "grid_position": 1, "finish_position": 1, "finished": True},
        {"round": 1, "location": "Monaco", "driver": "LEC", "team": "Ferrari",  "grid_position": 2, "finish_position": 4, "finished": True},
        {"round": 2, "location": "Monza",  "driver": "VER", "team": "Red Bull", "grid_position": 3, "finish_position": 1, "finished": True},
        {"round": 2, "location": "Monza",  "driver": "LEC", "team": "Ferrari",  "grid_position": 1, "finish_position": 2, "finished": True},
    ])


def test_build_circuit_map_is_sorted_and_stable():
    cmap = build_circuit_map(_history())
    assert set(cmap) == {"Monaco", "Monza"}
    # Sorted order → Monaco before Monza → ids "0" and "1".
    assert cmap == {"Monaco": "0", "Monza": "1"}


def test_build_circuit_features_targets_delta():
    X, y, cmap = build_circuit_features(_history())
    # One row per history row.
    assert len(X) == 4
    assert list(X.columns) == ["grid_position", "circuit_encoded"]
    # delta = finish - grid: [1-1, 4-2, 1-3, 2-1] = [0, 2, -2, 1]
    assert list(y) == [0.0, 2.0, -2.0, 1.0]


def test_build_stage2_training_data_ranks_and_no_leakage():
    history = _history()
    df = build_stage2_training_data(history, practice_paces={}, quali_data={})
    # Round 1 has no prior rounds → default ranks; round 2 uses round-1 standings.
    assert set(STAGE2_FEATURES).issubset(df.columns)
    assert "position_delta" in df.columns
    assert len(df) == 4
    # Round 1 (first two rows): no prior races → championship_rank defaults to n_drivers (2).
    assert df.iloc[0]["championship_rank"] == 2.0
    # Round 2: VER led after round 1 (25 pts) → rank 1; LEC (12 pts) → rank 2.
    r2 = df.iloc[2:]
    ver_row = r2[r2["position_delta"] == (1 - 3)].iloc[0]  # VER grid 3 finish 1
    assert ver_row["championship_rank"] == 1.0


def test_build_prediction_features_shapes_and_columns():
    quali = pd.DataFrame([
        {"driver": "VER", "team": "Red Bull", "grid_position": 1},
        {"driver": "LEC", "team": "Ferrari",  "grid_position": 2},
    ])
    practice = pd.DataFrame([
        {"driver": "LEC", "practice_pace_s": -0.3},
        {"driver": "VER", "practice_pace_s": 0.1},
    ])
    d_stand = pd.DataFrame([{"driver": "VER", "driver_points": 25}, {"driver": "LEC", "driver_points": 12}])
    c_stand = pd.DataFrame([{"team": "Red Bull", "constructor_points": 25}, {"team": "Ferrari", "constructor_points": 12}])

    x_circuit, x_pace = build_prediction_features(
        quali, practice, "Monaco", {"Monaco": "0"}, d_stand, c_stand,
    )
    assert list(x_circuit["circuit_encoded"]) == ["0", "0"]
    assert set(STAGE2_FEATURES).issubset(x_pace.columns)
    # LEC has faster (lower) practice pace → fp2_pace_rank 1.
    lec = x_pace[x_pace["driver"] == "LEC"].iloc[0]
    assert lec["fp2_pace_rank"] == 1.0
    # VER leads championship → championship_rank 1.
    ver = x_pace[x_pace["driver"] == "VER"].iloc[0]
    assert ver["championship_rank"] == 1.0
