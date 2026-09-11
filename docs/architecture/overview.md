# Architecture overview

A single product in three layers: a React frontend, a FastAPI backend, and an
ML pipeline that reads cached F1 data.

## Request flow

```
User
  │  browser
  ▼
Vercel (React + Vite static build)
  │  fetch  VITE_API_URL/{races,predict,logo}
  ▼
Render (FastAPI, Docker)
  │
  ├─ routes/         HTTP concerns (health, races, predictions, logos)
  │      │
  │      ▼
  ├─ services/       application logic
  │      │  race_service.list_races / ff1_to_race_key
  │      │  prediction_service.generate_prediction  (+ in-memory cache)
  │      ▼
  └─ ml/             prediction pipeline
         │  predictor.run → features + model + data_loader
         ▼
     data/           committed pkl caches + FastF1 session cache
         │
         ▼
     Prediction response (JSON)  ──►  frontend visualization
```

## Backend module responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| Routes | `backend/app/routes/` | HTTP only — parse request, call a service, map errors to status codes. |
| Services | `backend/app/services/` | Application logic — schedule resolution, prediction orchestration, caching. |
| Schemas | `backend/app/schemas/` | Pydantic request/response models. |
| Constants | `backend/app/constants.py` | Circuit metadata, round map, logo slugs (presentation data). |
| Config | `backend/app/config.py` | CORS origins, title, logo cache dir (env-driven). |
| ML | `ml/` | Prediction only — imported by services, never the reverse. |

The dependency direction is strict: `routes → services → ml`. The ML package
knows nothing about the web layer.

## Endpoints (contract)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness probe (Render health check). |
| GET | `/races?year=YYYY` | Completed + current races, resolved to circuit keys. |
| POST | `/predict` | Run (or serve cached) prediction for `{race, year, force_refresh}`. |
| GET | `/logo/{slug}` | Proxy + cache team logos from the F1 CDN. |

## Deployment

- **Frontend → Vercel** — static build, `VITE_API_URL` points at the Render API.
- **Backend → Render** — Docker image (`Dockerfile`, `render.yaml`) with the
  pre-warmed `data/` pkl caches baked in, so the server starts warm.

Paths are resolved in `ml/config.py` and overridable with `F1_DATA_DIR` /
`F1_CACHE_DIR`; CORS via `CORS_ORIGINS`. See `.env.example`.
