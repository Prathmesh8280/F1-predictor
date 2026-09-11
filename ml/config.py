"""Centralised paths and settings for the ML pipeline.

All filesystem locations are resolved here so the rest of the package never
hardcodes a path. Values can be overridden by environment variables for
deployment, but default to the repo-local layout that ships pre-warmed caches.
"""
import os

# Repo root = parent of the ml/ package directory.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directory. Holds committed pkl caches + FastF1 session subdirectories.
# Override with F1_DATA_DIR (e.g. a mounted volume on a cloud host).
DATA_DIR = os.environ.get("F1_DATA_DIR", os.path.join(ROOT_DIR, "data"))

# FastF1 + application pickle cache. Kept equal to DATA_DIR to preserve the
# warm-start layout that is baked into the Docker image; override separately
# with F1_CACHE_DIR only if the cache must live apart from committed data.
CACHE_DIR = os.environ.get("F1_CACHE_DIR", DATA_DIR)

# Walk-forward backtest summary written by ml/backtest.py, read at predict time.
BACKTEST_SUMMARY = os.path.join(DATA_DIR, "backtest_summary.json")

# Team logo binary cache (downloaded from the F1 CDN on first request).
LOGOS_DIR = os.path.join(CACHE_DIR, "logos")
