"""Deterministic tests for pure backtest scoring helpers (no network)."""
import numpy as np
import pandas as pd

from ml.backtest import _blended_positions, _subset_metrics


def _frame():
    # pred1 = Stage 1 delta; pred2 = Stage 2 rank.
    return pd.DataFrame({
        "grid_position":   [1.0, 2.0, 3.0, 4.0],
        "pred1":           [0.0, 0.0, 0.0, 0.0],   # no circuit adjustment
        "pred2":           [4.0, 3.0, 2.0, 1.0],   # reverse of grid
        "finish_position": [1.0, 2.0, 3.0, 4.0],
        "finished":        [True, True, True, True],
    })


def test_blend_alpha_1_is_pure_circuit_rank():
    frame = _frame()
    pos = _blended_positions(frame, alpha=1.0)
    # circuit_adjusted = grid + pred1 = [1,2,3,4] → ranks [1,2,3,4].
    assert list(pos) == [1.0, 2.0, 3.0, 4.0]


def test_blend_alpha_0_is_pure_stage2_rank():
    frame = _frame()
    pos = _blended_positions(frame, alpha=0.0)
    # pure stage2 rank = pred2 = [4,3,2,1].
    assert list(pos) == [4.0, 3.0, 2.0, 1.0]


def test_blend_half_is_average_of_the_two_ranks():
    frame = _frame()
    pos = _blended_positions(frame, alpha=0.5)
    # 0.5*[1,2,3,4] + 0.5*[4,3,2,1] = [2.5, 2.5, 2.5, 2.5]
    assert list(pos) == [2.5, 2.5, 2.5, 2.5]


def test_blend_falls_back_to_circuit_rank_when_stage2_missing():
    frame = _frame()
    frame["pred2"] = [np.nan, np.nan, np.nan, np.nan]
    pos = _blended_positions(frame, alpha=0.0)
    # Any NaN in pred2 → pure circuit rank regardless of alpha.
    assert list(pos) == [1.0, 2.0, 3.0, 4.0]


def test_subset_metrics_perfect_prediction():
    frame = _frame()
    # positions exactly equal to finish order → model MAE 0, perfect Spearman.
    positions = frame["finish_position"].values
    m = _subset_metrics(frame, positions)
    assert m["model_mae"] == 0.0
    assert m["model_spearman"] == 1.0
    assert m["podium_hit"] == 1.0
