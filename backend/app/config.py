"""Backend API configuration (environment-driven)."""
import os

from ml.config import LOGOS_DIR

TITLE = "F1 Predictor API"

# CORS allowed origins. Comma-separated via CORS_ORIGINS, or "*" for all.
_origins = os.environ.get("CORS_ORIGINS", "*").strip()
CORS_ORIGINS = ["*"] if _origins == "*" else [o.strip() for o in _origins.split(",") if o.strip()]

# The team logo binary cache lives under the ML data directory.
os.makedirs(LOGOS_DIR, exist_ok=True)
