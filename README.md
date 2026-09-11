# F1 Race Predictor

A Formula 1 race prediction web app. Given qualifying results and practice session data, a two-stage machine learning pipeline predicts each driver's finishing position. Results are served via a FastAPI backend and displayed in a React frontend with animated visualisations.

Live at: *(deploy URL here)*

---

## How it works

The model is split into two stages:

**Stage 1 — Circuit baseline** (trained on 2024–2025 seasons)
Learns how grid position translates to finish position at each specific circuit via a grid×circuit interaction. Each track gets its own grid slope, regularised toward a global slope. Circuit layout doesn't change with rule changes, so prior seasons are valid training data.

**Stage 2 — Current pace & form** (trained on the current season only)
Learns who is actually fast under 2026 regulations using:
- Qualifying gap to pole (seconds behind the fastest qualifier)
- FP2 long-run pace — gap to fastest and race-pace rank (median lap on race compounds, TyreLife > 3)
- Sprint race lap times on sprint weekends (used instead of FP2)
- Driver and team average finish position this season so far

Stage 2 carries **no direct grid anchor** — backtest showed that anchoring to grid made it echo the qualifying order. Keeping it to pace + form lets it predict genuine position changes.

**Final prediction = 60% Stage 1 + 40% Stage 2** (blend weight chosen by walk-forward backtest)

---

## Evaluation

Validated with a **walk-forward backtest** — for each race, the model is trained only on data available *before* that race, then scored against the actual result. All metrics are **out-of-sample** over 36 races (2024–2026).

The headline metric is **finishers-only MAE**: error over drivers who completed the race, with DNFs excluded. DNFs are irreducible noise — no pre-race feature predicts an engine failure — and finishers-only MAE measures what is actually predictable.

| Metric | Model | Grid-order baseline |
|---|---|---|
| **Finishers-only MAE (positions)** | **2.08** | 2.19 |
| Finishers Spearman correlation | **0.81** | — |
| All-drivers MAE (positions) | 3.40 | 3.39 |
| Podium hit rate | 74% | — |

On the predictable part of the race (classified finishers), the model **beats a "qualifying order holds" baseline by ~0.11 positions** — a small but robust margin, consistent across a broad range of blend weights.

---

## Project structure

```
F1-predictor/
├── backend/
│   ├── api.py               # FastAPI app — /races, /predict, /logo endpoints
│   └── requirements.txt     # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/             # Fetch wrappers (client.ts)
│   │   ├── components/race/ # All race UI components (PredictionTable, GridFlowViz, etc.)
│   │   ├── constants/       # Circuit metadata, driver info, overtaking config
│   │   ├── hooks/           # useInView hook
│   │   ├── lib/             # Prediction signal helpers
│   │   ├── pages/           # RacesPage (main), HowItWorksPage, AboutPage
│   │   └── types/           # Shared TypeScript types
│   ├── vercel.json          # Vercel SPA routing
│   └── package.json
├── src/
│   ├── data_loader.py       # FastF1 fetching — results, qualifying, FP2/sprint pace
│   ├── features.py          # Feature engineering for Stage 1 and Stage 2
│   ├── model.py             # Two-stage Ridge regression and blended prediction
│   ├── predictor.py         # Pipeline orchestration
│   ├── backtest.py          # Walk-forward out-of-sample evaluation
│   └── experiments.py       # Feature and model bake-off
├── data/                    # Pre-baked pkl caches (committed — warm cold start)
├── Dockerfile               # Backend image for Render
├── render.yaml              # Render deployment config
└── requirements.txt         # Root ML/data dependencies
```

---

## Local development

### Backend

```bash
pip install -r backend/requirements.txt
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

The backend serves on `http://localhost:8000`. Qualifying data for the current race is fetched and cached on the first `/predict` call.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on `http://localhost:5173` and proxies all API calls to `localhost:8000`.

---

## Deployment

- **Backend → Render** (Docker, `render.yaml` provided)
- **Frontend → Vercel** (static build, `vercel.json` provided)

Set `VITE_API_URL` in Vercel's environment variables to the Render backend URL before deploying the frontend.

Pre-baked pkl caches in `data/` are committed and included in the Docker image so the server starts warm — no cold-download delay on first request.

### Updating after each race weekend

After a race completes, run the following to refresh the cache and push warm data:

```bash
# Force-refresh the current season history and the completed race's data
python -c "from src.data_loader import load_history; load_history((2026,), force_refresh=True)"

# Then commit the updated pkls
git add data/*.pkl
git commit -m "Update 2026 cache post-{Race} GP (R{N})"
git push
```

Render will redeploy automatically on push.

---

## Data sources

| Data | Source | Used for |
|---|---|---|
| Race results (2024–2025) | FastF1 | Stage 1 circuit pattern training |
| Race results (2026) | FastF1 | Stage 2 driver/team form |
| Starting grid (penalty-corrected) | OpenF1 `/v1/starting_grid` | Accurate pre-race grid positions |
| Qualifying session | FastF1 | Gap-to-pole feature |
| FP2 laps / Sprint laps | FastF1 | Race pace proxy |
| Actual results (post-race) | FastF1 | Post-race comparison view |
| Team logos | Formula1.com CDN | Frontend team badges |
| Circuit maps | Formula1.com CDN | Circuit context section |

---

## Backtest commands

```bash
python -m src.backtest          # Out-of-sample metrics vs grid baseline
python -m src.backtest --tune   # Sweep blend weight
python -m src.experiments       # Stage 2 feature + model bake-off
python -m src.experiments --stage1   # A/B Stage 1 training scope
```
