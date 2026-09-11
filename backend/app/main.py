"""FastAPI application entrypoint.

Run with:  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
"""
import fastf1
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ml.config import CACHE_DIR

from backend.app import config
from backend.app.routes import health, logos, predictions, races

fastf1.Cache.enable_cache(str(CACHE_DIR))

app = FastAPI(title=config.TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(races.router)
app.include_router(predictions.router)
app.include_router(logos.router)
