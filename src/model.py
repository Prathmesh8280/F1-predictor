import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error

from src.features import STAGE1_FEATURES, STAGE2_FEATURES


class GridCircuitInteraction(BaseEstimator, TransformerMixin):
    """Add per-circuit grid slopes on top of a global grid slope.

    Input columns (from the Stage 1 ColumnTransformer, in order) are the scaled
    grid position followed by the one-hot circuit columns. This appends the
    products grid * each-circuit-column, so the downstream Ridge fits:

        finish ~ global_slope * grid              (shared across circuits)
               + circuit_offset                   (one-hot: per-circuit intercept)
               + circuit_slope * grid             (interaction: per-circuit slope)

    Ridge's L2 penalty shrinks the per-circuit offsets and slope deviations
    toward zero, i.e. sparse circuits fall back to the global grid slope. An
    unknown circuit at predict time is all-zeros, so it uses the global slope.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        grid = X[:, [0]]          # scaled grid position
        onehot = X[:, 1:]         # one-hot circuit columns
        return np.hstack([grid, onehot, onehot * grid])

# Weight on grid rank vs pace rank in the final blend.
# score = alpha * grid_rank + (1 - alpha) * pace_rank
# alpha=0 → pure pace order (pace decides the race)
# alpha=1 → pure grid order (qualifying decides the race)
# Re-tune with: python -m src.backtest --tune  (optimises Spearman, not MAE)
BLEND_ALPHA = 0.60

# Within Stage 2: weights for the three signals (auto-normalised if any missing).
# driver_champ = driver's cumulative championship points this season
# constructor  = constructor championship points (team baseline)
# fp2          = current weekend FP2 / Sprint long-run pace (circuit-specific signal)
DRIVER_CHAMP_WEIGHT      = 0.35
CONSTRUCTOR_CHAMP_WEIGHT = 0.35
FP2_WEIGHT               = 0.30


def train_stage1(X: pd.DataFrame, y: np.ndarray, verbose: bool = True):
    """Ridge regression on circuit + grid features (2024-2025 historical data).

    One-hot encodes the circuit, then the GridCircuitInteraction step gives
    each track its own grid slope on top of a shared global slope (so "P1 at
    Monaco" and "P1 at Monza" can map to finish differently). handle_unknown=
    'ignore' means an unseen circuit at prediction time maps to all-zeros — the
    model falls back to the global grid slope alone.
    """
    preprocessor = ColumnTransformer([
        ("grid", StandardScaler(), ["grid_position"]),
        ("circuit", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["circuit_encoded"]),
    ])

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("interaction", GridCircuitInteraction()),
        ("ridge", Ridge(alpha=10.0)),
    ])

    pipeline.fit(X[STAGE1_FEATURES], y)

    if verbose:
        mae = mean_absolute_error(y, pipeline.predict(X[STAGE1_FEATURES]))
        print(f"  Stage 1 trained. In-sample delta MAE: {mae:.2f} positions")
    return pipeline


def train_stage2(X: pd.DataFrame, y: np.ndarray, features=None, estimator=None, verbose: bool = True):
    """Regression on current-season pace features (current year only).

    features  : column subset to train on (defaults to STAGE2_FEATURES).
    estimator : any sklearn regressor (defaults to Ridge(alpha=5.0)); cloned
                so the same template can be reused across walk-forward folds.

    SimpleImputer fills missing values (e.g. no practice data, first race
    of season where form is unknown) with the column median before scaling.
    The fitted pipeline selects its columns by name, so prediction can be
    handed the full feature frame regardless of the subset used.
    """
    features = list(STAGE2_FEATURES if features is None else features)
    estimator = Ridge(alpha=5.0) if estimator is None else clone(estimator)

    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), features),
    ])

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    pipeline.fit(X[features], y)

    if verbose:
        mae = mean_absolute_error(y, pipeline.predict(X[features]))
        print(f"  Stage 2 trained. In-sample delta MAE: {mae:.2f} positions")
    return pipeline
