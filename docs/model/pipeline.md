# ML prediction pipeline

The model predicts each driver's finishing position from the qualifying grid,
season form, and practice pace. It is a two-stage blend, orchestrated by
`ml/predictor.run()`.

## Data flow

```
FastF1 / OpenF1
  │  ml/data_loader.py
  ├─ load_history(years)        → race results (Stage 1 + form)
  ├─ load_qualifying(year,race) → penalty-corrected grid (OpenF1 → FastF1 fallback)
  └─ load_practice_pace(...)    → FP2 / Sprint race-pace proxy
        │  (all cached as data/*.pkl)
        ▼
  ml/features.py   → build_circuit_features / build_stage2_training_data / build_prediction_features
        ▼
  ml/model.py      → train_stage1 (circuit) + train_stage2 (pace/form)
        ▼
  ml/predictor.py  → blend + rank → predicted finishing order
```

## Stage 1 — circuit baseline

Trained on prior seasons (2024–2025). Learns how grid position maps to a
finish-position **delta** at each circuit, via a grid×circuit interaction
(`GridCircuitInteraction` in `model.py`). Each track gets its own grid slope,
regularised toward a global slope, so sparse/unseen circuits fall back to the
global pattern. Regulation-era agnostic — circuit layout doesn't change with
rules.

## Stage 2 — current pace & form

Trained on the current season only. Three rank features (all 1..N, lower =
better): `championship_rank`, `constructor_rank`, `fp2_pace_rank`. No direct
grid anchor — the backtest showed anchoring to grid just echoes qualifying.

## Blend

`final = 0.60 · Stage 1 + 0.40 · Stage 2` (`BLEND_ALPHA` in `model.py`), then
re-ranked to a finishing order. Weight tuned by the walk-forward backtest.

## Evaluation

`ml/backtest.py` runs a walk-forward (time-based) backtest: for each race, train
only on data available before it, then score. Headline metric is
**finishers-only MAE** (DNFs excluded as irreducible noise). Latest: 2.08 vs a
2.19 grid-order baseline over 36 races. Re-tune the blend with
`python -m ml.backtest --tune`.

## Caching & freshness

History pkl keys embed the completed-round count
(`history_2026_r13_v3.pkl`), so a new race automatically invalidates the cache.
Per-race qualifying/practice are cached individually. See
[`data/README.md`](../../data/README.md).
