import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error

from src.features import STAGE1_FEATURES, STAGE2_FEATURES

# How much weight goes to the circuit baseline vs the current-pace model.
# 0.35 circuit + 0.65 pace: favour current-season data since regs changed.
BLEND_ALPHA = 0.35


def train_stage1(X: pd.DataFrame, y: np.ndarray):
    """Ridge regression on circuit + grid features (2024-2025 historical data).

    One-hot encodes the circuit so each track gets its own intercept offset,
    then fits a single grid_position slope on top. handle_unknown='ignore'
    means an unseen circuit at prediction time maps to all-zeros — the model
    falls back to grid position alone.
    """
    preprocessor = ColumnTransformer([
        ("grid", StandardScaler(), ["grid_position"]),
        ("circuit", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["circuit_encoded"]),
    ])

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("ridge", Ridge(alpha=10.0)),
    ])

    pipeline.fit(X[STAGE1_FEATURES], y)

    mae = mean_absolute_error(y, pipeline.predict(X[STAGE1_FEATURES]))
    print(f"  Stage 1 trained. In-sample MAE: {mae:.2f} positions")
    return pipeline


def train_stage2(X: pd.DataFrame, y: np.ndarray):
    """Ridge regression on current-season pace features (2026 data only).

    SimpleImputer fills missing values (e.g. no practice data, first race
    of season where form is unknown) with the column median before scaling.
    """
    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), STAGE2_FEATURES),
    ])

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("ridge", Ridge(alpha=5.0)),
    ])

    pipeline.fit(X[STAGE2_FEATURES], y)

    mae = mean_absolute_error(y, pipeline.predict(X[STAGE2_FEATURES]))
    print(f"  Stage 2 trained. In-sample MAE: {mae:.2f} positions")
    return pipeline


def predict_blended(
    stage1_model,
    stage2_model,
    x_circuit: pd.DataFrame,
    x_pace: pd.DataFrame,
    alpha: float = BLEND_ALPHA,
) -> np.ndarray:
    """Blend Stage 1 (circuit baseline) and Stage 2 (current pace) predictions.

    alpha=0.35 means 35% circuit baseline, 65% current pace.
    """
    pred1 = stage1_model.predict(x_circuit[STAGE1_FEATURES])
    pred2 = stage2_model.predict(x_pace[STAGE2_FEATURES])
    return alpha * pred1 + (1 - alpha) * pred2
