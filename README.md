# F1 Race Predictor

A Formula 1 race prediction web app. A two-stage machine learning pipeline
predicts each driver's finishing position from qualifying, practice pace, and
season form. Served by a FastAPI backend and a React + TypeScript frontend with
animated visualisations.

Live at: *(deploy URL here)*

---

## Repository structure

```
F1-predictor/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py          # App entrypoint (uvicorn backend.app.main:app)
│   │   ├── config.py        # CORS, title, cache dir (env-driven)
│   │   ├── constants.py     # Circuit metadata, round map, logo slugs
│   │   ├── routes/          # HTTP layer: health, races, predictions, logos
│   │   ├── services/        # App logic: race_service, prediction_service
│   │   └── schemas/         # Pydantic request/response models
│   ├── tests/               # pytest — routes + services (no network)
│   └── requirements.txt     # Deployed API dependency set
├── ml/                      # Prediction pipeline (imported by the backend)
│   ├── config.py            # Central data/cache paths (F1_DATA_DIR overridable)
│   ├── data_loader.py       # FastF1 + OpenF1 fetching, pkl caching
│   ├── features.py          # Feature engineering (Stage 1 + Stage 2)
│   ├── model.py             # Two-stage Ridge regression
│   ├── predictor.py         # Pipeline orchestration (run())
│   ├── backtest.py          # Walk-forward out-of-sample evaluation
│   └── tests/               # pytest — features, model, predictor, backtest
├── frontend/                # React + Vite + Tailwind
│   ├── src/                 # api/ components/ constants/ hooks/ lib/ pages/ types/
│   └── tests/               # vitest — signals, round map, API client
├── scripts/
│   ├── download_data.py     # Download raw season history
│   ├── rebuild_cache.py     # Warm all caches (post-race update)
│   ├── run_prediction.py    # Headless single-race prediction (CLI)
│   └── legacy/              # Superseded Streamlit UI + Plotly CLI (kept for reference)
├── data/                    # Committed pkl caches (warm cold-start) — see data/README.md
├── docs/                    # architecture/ + model/
├── Dockerfile, render.yaml  # Backend deploy (Render)
├── frontend/vercel.json     # Frontend deploy (Vercel)
├── pyproject.toml           # Metadata + pytest config
└── .env.example             # Environment variable reference
```

---

## How it works

**Stage 1 — circuit baseline** (2024–2025): learns how grid position maps to a
finish-position delta at each circuit, with a per-circuit grid slope regularised
toward a global slope.

**Stage 2 — current pace & form** (current season): three rank features —
qualifying/championship/constructor standing and FP2 long-run pace. No direct
grid anchor.

**Final = 60% Stage 1 + 40% Stage 2**, re-ranked to a finishing order. Blend
weight tuned by a walk-forward backtest. Full detail in
[docs/model/pipeline.md](docs/model/pipeline.md); system design in
[docs/architecture/overview.md](docs/architecture/overview.md).

Latest out-of-sample result: **2.08 finishers-only MAE** vs a 2.19 grid-order
baseline over 36 races.

---

## Local development

### Backend

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Serves on `http://localhost:8000`. Endpoints: `/health`, `/races`, `/predict`,
`/logo/{slug}`.

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies API to :8000
```

---

## Tests

```bash
# Python (backend + ml) — deterministic, no network
pip install -r backend/requirements.txt pytest httpx
pytest

# Frontend
cd frontend
npm run typecheck
npm run test
```

CI runs all of the above on push/PR — see `.github/workflows/test.yml`.

---

## ML / data scripts

```bash
python scripts/run_prediction.py --race Italy --year 2026   # headless prediction
python scripts/rebuild_cache.py --stage2                     # refresh current season
python scripts/download_data.py --years 2024 2025            # download raw history
python -m ml.backtest                                        # out-of-sample metrics
python -m ml.backtest --tune                                 # sweep blend weight
```

---

## Deployment

- **Backend → Render** (Docker, `render.yaml`). Pre-baked `data/` pkl caches are
  copied into the image so the server starts warm.
- **Frontend → Vercel** (static build, `frontend/vercel.json`). Set
  `VITE_API_URL` to the Render backend URL.

Configuration is environment-driven — see [.env.example](.env.example).

### Updating after each race weekend

```bash
python scripts/rebuild_cache.py --stage2   # refresh current-season data
git add data/*.pkl
git commit -m "Update 2026 cache post-{Race} GP (R{N})"
git push                                    # Render redeploys automatically
```

---

## Data sources

| Data | Source | Used for |
|---|---|---|
| Race results (2024–2025) | FastF1 | Stage 1 circuit pattern training |
| Race results (current) | FastF1 | Stage 2 driver/team form |
| Starting grid (penalty-corrected) | OpenF1 | Accurate pre-race grid positions |
| Qualifying session | FastF1 | Gap-to-pole feature |
| FP2 / Sprint laps | FastF1 | Race pace proxy |
| Actual results (post-race) | FastF1 | Post-race comparison view |
| Team logos / circuit maps | Formula1.com CDN | Frontend assets |
