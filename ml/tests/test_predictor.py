"""Deterministic tests for reusable predictor seams (no network / FastF1)."""
import pandas as pd

from ml.predictor import build_circuit_model, compute_championship_standings


def test_championship_standings_points_math():
    # VER: 1st (25) + 2nd (18) = 43. LEC: 2nd (18) + 1st (25) = 43. HAM: 3rd (15) + 3rd (15) = 30.
    history = pd.DataFrame([
        {"driver": "VER", "team": "Red Bull", "finish_position": 1},
        {"driver": "LEC", "team": "Ferrari",  "finish_position": 2},
        {"driver": "HAM", "team": "Ferrari",  "finish_position": 3},
        {"driver": "VER", "team": "Red Bull", "finish_position": 2},
        {"driver": "LEC", "team": "Ferrari",  "finish_position": 1},
        {"driver": "HAM", "team": "Ferrari",  "finish_position": 3},
    ])
    drivers, constructors = compute_championship_standings(history)

    d = dict(zip(drivers["driver"], drivers["driver_points"]))
    assert d == {"VER": 43, "LEC": 43, "HAM": 30}

    c = dict(zip(constructors["team"], constructors["constructor_points"]))
    # Ferrari = LEC(43) + HAM(30) = 73; Red Bull = VER(43).
    assert c == {"Ferrari": 73, "Red Bull": 43}


def test_championship_standings_empty_for_no_history():
    drivers, constructors = compute_championship_standings(pd.DataFrame())
    assert drivers.empty and constructors.empty
    assert list(drivers.columns) == ["driver", "driver_points"]
    assert list(constructors.columns) == ["team", "constructor_points"]


def test_finish_outside_points_scores_zero():
    history = pd.DataFrame([
        {"driver": "ALB", "team": "Williams", "finish_position": 15},  # no points
        {"driver": "VER", "team": "Red Bull", "finish_position": 1},   # 25
    ])
    drivers, _ = compute_championship_standings(history)
    d = dict(zip(drivers["driver"], drivers["driver_points"]))
    assert d["ALB"] == 0
    assert d["VER"] == 25


def test_build_circuit_model_returns_fitted_model_and_map():
    history = pd.DataFrame([
        {"location": "Monza", "grid_position": g, "finish_position": g}
        for g in range(1, 21)
    ])
    model, cmap = build_circuit_model(history, verbose=False)
    assert "Monza" in cmap
    # finish == grid everywhere → deltas all 0 → predictions near 0.
    import numpy as np
    x = pd.DataFrame({"grid_position": [5.0], "circuit_encoded": [cmap["Monza"]]})
    assert abs(float(model.predict(x)[0])) < 1.0
