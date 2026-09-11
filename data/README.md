# Data directory

This directory holds all cached F1 data. Paths are resolved centrally in
[`ml/config.py`](../ml/config.py) and can be overridden with `F1_DATA_DIR`.

## Current layout

Pickle caches live flat in this directory and are **committed to git** so a
fresh deploy starts warm (no multi-minute FastF1 cold-download on first request):

| Pattern | Contents |
|---|---|
| `history_{years}_r{N}_v3.pkl` | Race-result history for training. `r{N}` = completed-round count, so a new race auto-invalidates the cache. |
| `quali_{year}_{race}.pkl` | Penalty-corrected qualifying grid per race. |
| `practice_{year}_{race}.pkl` | FP2 / Sprint race-pace proxy per race. |
| `{year}/` | FastF1's own session cache (SQLite + per-session files). Git-ignored. |
| `logos/` | Team logo binaries downloaded from the F1 CDN. Git-ignored. |

## Convention directories

`raw/`, `processed/`, and `cache/` exist as conventional locations for future
data organization. They are currently empty placeholders — the live pipeline
still reads and writes the flat layout above to preserve the warm-start deploy.
Any migration into these folders should go through `ml/config.py` so no code
hardcodes a path.
