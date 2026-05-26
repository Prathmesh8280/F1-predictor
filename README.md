# F1 Predictor

A Formula 1 race result predictor using a two-stage machine learning pipeline. Given qualifying results and practice session data, it predicts the finishing order for an upcoming (or completed) race and renders an interactive chart in your browser.

---

## How it works

The model is split into two stages that answer different questions:

**Stage 1 — Circuit baseline** (trained on 2024–2025)
Learns how grid position translates to finish position at each specific circuit. Monaco keeps the field bunched; Monza sees more movement. This stage is regulation-era agnostic — circuit layout doesn't change with rule changes.

**Stage 2 — Current pace** (trained on 2026 races only)
Learns who is actually fast under the current regulations using:
- Qualifying gap to pole (seconds behind the fastest qualifier)
- FP2 long-run pace (median lap time on race compounds, TyreLife > 3)
- Sprint race lap times on sprint weekends (used instead of FP2)
- Driver and team average finish position in 2026 so far

**Final prediction = 35% Stage 1 + 65% Stage 2**

The 2026 weighting is higher because regulation changes mean 2024–2025 team performance is no longer a reliable signal — only circuit characteristics carry over.

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
    └── predictor.py     # Pipeline orchestration
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
