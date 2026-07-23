"""
Pre-build all data caches so app predictions are instant.

Stage 1 cache  (2024+2025 history)  — build once on first deployment, never changes.
Stage 2 cache  (2026 per-round)     — run again after each race weekend to pick up
                                       the new race result, qualifying, and FP2 data.

Usage:
  python warm_cache.py              # warm everything not yet cached
  python warm_cache.py --refresh    # force re-download from FastF1 (full refresh)
  python warm_cache.py --stage2     # refresh 2026 data only (post-race update)
"""
import argparse
import os
import time

import fastf1
import pandas as pd
from datetime import datetime, timezone

from src.data_loader import load_history, load_qualifying, load_practice_pace, CACHE_DIR


def _completed_rounds(year: int) -> list[int]:
    """Return round numbers for all completed races in a given season."""
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        now = datetime.now(timezone.utc)
        completed = schedule[
            (schedule["EventFormat"] != "testing")
            & (schedule["RoundNumber"] > 0)
            & (pd.to_datetime(schedule["EventDate"], utc=True) < now)
        ]
        return sorted(completed["RoundNumber"].tolist())
    except Exception as e:
        print(f"  Warning: could not fetch {year} schedule: {e}")
        return []


def warm_stage1(force: bool = False):
    """Cache 2024+2025 historical race results (Stage 1 training data)."""
    print("\n── Stage 1: historical data (2024 + 2025) ─────────────────────")
    t = time.time()
    load_history(train_years=(2024, 2025), force_refresh=force)
    print(f"   Done ({time.time() - t:.1f}s)")


def warm_stage2(year: int = 2026, force: bool = False):
    """Cache current-season history + per-round qualifying and FP2 data."""
    print(f"\n── Stage 2: {year} season data ────────────────────────────────")

    # Season-level history (all completed races this year)
    t = time.time()
    print(f"  Refreshing {year} race history...")
    load_history(train_years=(year,), force_refresh=force)
    print(f"  Done ({time.time() - t:.1f}s)")

    # Per-round qualifying + FP2 for each completed race
    rounds = _completed_rounds(year)
    if not rounds:
        print(f"  No completed rounds found for {year}.")
        return

    print(f"\n  Warming {len(rounds)} completed round(s): {rounds}")
    for rnd in rounds:
        print(f"\n  Round {rnd}:")
        t = time.time()
        try:
            load_qualifying(year, rnd, force_refresh=force)
            print(f"    Qualifying  ({time.time() - t:.1f}s)")
        except Exception as e:
            print(f"    Qualifying  FAILED: {e}")

        t = time.time()
        try:
            load_practice_pace(year, rnd, force_refresh=force)
            print(f"    FP2/Sprint  ({time.time() - t:.1f}s)")
        except Exception as e:
            print(f"    FP2/Sprint  FAILED: {e}")


def main():
    parser = argparse.ArgumentParser(description="Pre-build F1 predictor data caches.")
    parser.add_argument(
        "--refresh", action="store_true",
        help="Force re-download from FastF1, ignoring existing cache files."
    )
    parser.add_argument(
        "--stage2", action="store_true",
        help="Refresh Stage 2 (current season) data only. Use this after each race weekend."
    )
    args = parser.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)

    total = time.time()

    if args.stage2:
        warm_stage2(force=args.refresh)
    else:
        warm_stage1(force=args.refresh)
        warm_stage2(force=args.refresh)

    print(f"\n{'='*55}")
    print(f"  Cache warm complete ({time.time() - total:.1f}s total)")
    print(f"  Cache directory: {os.path.abspath(CACHE_DIR)}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
