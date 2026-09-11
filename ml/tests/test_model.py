"""Deterministic tests for the two-stage models — output shape and validity."""
import numpy as np
import pandas as pd

from ml.features import STAGE2_FEATURES
from ml.model import train_stage1, train_stage2


def test_stage1_predicts_one_value_per_row_and_finite():
    X = pd.DataFrame({
        "grid_position": [1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0],
        "circuit_encoded": ["0", "0", "0", "0", "1", "1", "1", "1"],
    })
    y = np.array([0.0, 0.0, -1.0, 1.0, 0.0, 1.0, -1.0, 0.0])  # deltas
    model = train_stage1(X, y, verbose=False)
    preds = model.predict(X)
    assert preds.shape == (len(X),)
    assert np.all(np.isfinite(preds))


def test_stage1_unknown_circuit_falls_back_to_global_slope():
    X = pd.DataFrame({
        "grid_position": [1.0, 2.0, 3.0, 4.0],
        "circuit_encoded": ["0", "0", "1", "1"],
    })
    y = np.array([0.0, 1.0, -1.0, 0.0])
    model = train_stage1(X, y, verbose=False)
    # Unseen circuit id → one-hot all zeros → global slope only, still finite.
    unknown = pd.DataFrame({"grid_position": [2.0], "circuit_encoded": ["999"]})
    pred = model.predict(unknown)
    assert pred.shape == (1,)
    assert np.isfinite(pred[0])


def test_stage2_predicts_one_value_per_row_and_finite():
    X = pd.DataFrame({
        "championship_rank": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "constructor_rank":  [1.0, 1.0, 2.0, 2.0, 3.0, 3.0],
        "fp2_pace_rank":     [2.0, 1.0, 4.0, 3.0, 6.0, 5.0],
    })
    y = np.array([-1.0, 0.0, 1.0, 0.0, 2.0, -1.0])
    model = train_stage2(X, y, verbose=False)
    preds = model.predict(X[STAGE2_FEATURES])
    assert preds.shape == (len(X),)
    assert np.all(np.isfinite(preds))


def test_stage2_imputes_missing_features():
    X = pd.DataFrame({
        "championship_rank": [1.0, 2.0, 3.0, 4.0],
        "constructor_rank":  [1.0, 1.0, 2.0, 2.0],
        "fp2_pace_rank":     [1.0, np.nan, 3.0, np.nan],  # missing practice data
    })
    y = np.array([-1.0, 0.0, 1.0, 0.0])
    model = train_stage2(X, y, verbose=False)
    preds = model.predict(X[STAGE2_FEATURES])
    assert np.all(np.isfinite(preds))  # imputer handled the NaNs
