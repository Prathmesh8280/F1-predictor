# F1 Predictor

A Formula 1 race result predictor using a two-stage machine learning pipeline. Given qualifying results and practice session data, it predicts the finishing order for an upcoming (or completed) race and renders an interactive chart in your browser.

---

## How it works

The model is split into two stages that answer different questions:

**Stage 1 — Circuit baseline** (trained on prior seasons, e.g. 2024–2025)
Learns how grid position translates to finish position *at each specific circuit*, via a grid×circuit interaction (each track gets its own grid slope, regularised toward a global slope). Circuits are keyed on track **location**, so "Barcelona", "Canada", "Vegas" all resolve correctly. This stage is regulation-era agnostic — circuit layout doesn't change with rule changes.

**Stage 2 — Current pace & form** (trained on the current season only)
Learns who is actually fast under the current regulations using:
- Qualifying gap to pole (seconds behind the fastest qualifier)
- FP2 long-run pace — gap to fastest and race-pace rank (median lap on race compounds, TyreLife > 3)
- Sprint race lap times on sprint weekends (used instead of FP2)
- Driver and team average finish position this season so far

Stage 2 deliberately carries **no direct grid anchor** (no grid position / qualifying rank): the backtest showed that anchoring it to grid just made it echo the qualifying order. Keeping it to pace + form lets it predict genuine position changes.

**Final prediction = 60% Stage 1 + 40% Stage 2** (blend weight tuned by backtest — see below)

The Stage 2 feature set and the blend weight were both chosen by the walk-forward backtest, not by intuition.

---

## Evaluation

Predictions are validated with a **walk-forward (time-based) backtest**, not in-sample error. For each race in chronological order, the model is trained only on data available *before* that race — Stage 1 on prior seasons, Stage 2 on the same season's earlier rounds — then scored against the actual result. All metrics below are therefore **out-of-sample**, over 31 races (2025–2026). Comparisons are in rank space (re-ranked over the drivers common to prediction and result) to keep the model and the baseline on equal footing.

The headline metric is **finishers-only MAE**: error computed over the drivers who actually completed the race, with DNFs (retirements, crashes) excluded. DNFs are *irreducible noise* — no pre-race feature can predict an engine failure — and including them rewards a model for simply copying the grid (the safe hedge). Finishers-only MAE measures what's actually predictable: the racing order.

| Metric | Model | Grid-order baseline |
|---|---|---|
| **Finishers-only MAE (positions)** | **2.14** | 2.22 |
| Finishers Spearman correlation | **0.79** | — |
| All-drivers MAE (positions) | 3.46 | 3.47 |
| Podium hit rate | 72% | — |

**Headline:** on the predictable part of the race (classified finishers), the model **beats a "qualifying order holds" baseline by ~0.08 positions** — a small but robust margin, consistent across a broad range of blend weights. On all-drivers MAE it roughly ties grid, because that metric is dominated by unpredictable DNFs (~1.25 positions of pure noise). Grid position is an extremely strong predictor; the value here is a model that improves on it *where improvement is possible*, established by disciplined evaluation rather than an in-sample number.

How the configuration was chosen, all on the backtest:

- **Metric choice** — early tuning on all-drivers MAE drove the model to *copy the grid* (lowest average error = the safe hedge against DNFs). Switching to finishers-only MAE removed that perverse incentive and let the pace signal show through.
- **Blend weight** — sweeping the Stage 1/Stage 2 weight (`backtest.py --tune`) on finishers MAE settled at `0.60`.
- **Feature & model bake-off** — `experiments.py` compares Stage 2 feature sets and Ridge vs. RandomForest vs. gradient boosting. A pace/form Stage 2 with no grid anchor won; trees didn't beat Ridge by more than noise, so Ridge was kept for simplicity and generalisation on limited data.

```bash
python -m src.backtest          # out-of-sample metrics (all-drivers + finishers) vs grid
python -m src.backtest --tune   # sweep the blend weight (shows both objectives)
python -m src.experiments       # Stage 2 feature + model bake-off (finishers-scored)
python -m src.experiments --stage1   # A/B Stage 1 training scope
```

---

## Output

An interactive HTML chart opens in your browser showing:

- **GRID → PREDICTED** — bezier curves coloured by team, showing predicted position changes from qualifying
- **PREDICTED → ACTUAL** — dotted lines showing prediction error if the race has already finished (auto-detected)
- Hover over any line for driver details, team, and position change
- Click teams in the legend to isolate them
- Gold / silver / bronze highlights on podium positions
- Green ▲ = predicted to gain positions, Red ▼ = predicted to lose

The chart is saved as a standalone HTML file to `data/prediction_{year}_{race}.html`.

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py --race "Canada" --year 2026
```

### Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--race` | Yes | — | Race name, e.g. `"Canada"`, `"Monaco"`, `"Silverstone"` |
| `--year` | Yes | — | Race year, e.g. `2026` |
| `--train-years` | No | `2024 2025` | Seasons used for the circuit baseline model |
| `--refresh` | No | off | Force re-download of all cached data |

### Examples

```bash
# Predict an upcoming race
python main.py --race "British" --year 2026

# Predict a completed race (will also show actual results in the chart)
python main.py --race "Monaco" --year 2026

# Force refresh all cached data
python main.py --race "Canada" --year 2026 --refresh
```

---

## Project structure

```
F1-predictor/
├── main.py              # CLI entry point and Plotly visualisation
├── requirements.txt
└── src/
    ├── data_loader.py   # FastF1 data fetching — race results, qualifying, FP2/sprint pace
    ├── features.py      # Feature engineering for Stage 1 (circuit) and Stage 2 (pace)
    ├── model.py         # Two-stage Ridge regression models and blended prediction
    ├── predictor.py     # Pipeline orchestration (reusable train/predict seams)
    ├── backtest.py      # Walk-forward out-of-sample evaluation + blend-weight tuning
    └── experiments.py   # Stage 2 feature + model bake-off, scored on the backtest
```

---

## Data sources

All data is fetched automatically via the [FastF1](https://docs.fastf1.dev/) Python library. Sessions are cached locally in the `data/` directory on first load.

| Data | Source | Used for |
|---|---|---|
| Race results (2024–2025) | FastF1 | Stage 1 circuit pattern training |
| Race results (2026) | FastF1 | Stage 2 driver/team form |
| Qualifying session | FastF1 | Gap-to-pole feature |
| FP2 laps / Sprint laps | FastF1 | Race pace proxy |
| Actual results (post-race) | FastF1 | Chart comparison column |

---

## Dependencies

- `fastf1` — F1 session data
- `pandas` / `numpy` — data manipulation
- `scikit-learn` — Ridge regression, preprocessing pipelines
- `plotly` — interactive browser chart
- `matplotlib` — retained as a fastf1 dependency
