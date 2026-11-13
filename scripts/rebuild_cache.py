"""
Pre-build all data caches so app predictions are instant.

Stage 1 cache  (2024+2025 history)  — build once on first deployment, never changes.
Stage 2 cache  (2026 per-round)     — run again after each race weekend to pick up
                                       the new race result, qualifying, and FP2 data.

Usage:
  python scripts/rebuild_cache.py            # warm everything not yet cached
  python scripts/rebuild_cache.py --refresh  # force re-download from FastF1 (full refresh)
  python scripts/rebuild_cache.py --stage2   # refresh current-season data (post-race update)
"""
import argparse
import os
import sys
import time

# Ensure the repo root is importable when run as `python scripts/rebuild_cache.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fastf1
import pandas as pd
from datetime import datetime, timezone

from ml.data_loader import (
    load_history, load_qualifying, load_practice_pace,
    CACHE_DIR, _session_cache_path,
    normalise_location, normalize_name,
)


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


def _sync_postrace_grid(year: int, rnd: int):
    """Update qualifying caches using FastF1 race starting positions."""

    try:
        race_session = fastf1.get_session(year, rnd, "R")
        race_session.load(
            laps=False, telemetry=False,
            weather=False, messages=False
        )

        results = race_session.results

        if results is None or results.empty:
            print("    Race results unavailable; skipping grid update.")
            return False

        if pd.to_numeric(
            results["Position"], errors="coerce"
        ).notna().sum() == 0:
            print("    Race not completed; skipping.")
            return False

        positions = pd.to_numeric(
            results["GridPosition"], errors="coerce"
        )
        drivers = results["Abbreviation"].astype(str)

        # Never store an incomplete or fabricated starting grid.
        if not (
            drivers.ne("").all()
            and drivers.is_unique
            and positions.notna().all()
            and positions.gt(0).all()
            and (positions % 1 == 0).all()
            and positions.is_unique
        ):
            print("    Race grid incomplete; keeping existing caches.")
            return False

        grid_map = dict(zip(drivers, positions.astype(int)))

        event = fastf1.get_event(year, rnd)

        # Cover numeric round and normalised race-name caches.
        aliases = {
            str(rnd),
            normalize_name(
                normalise_location(event.get("Location", ""))
            ),
        }

        round_path = _session_cache_path("quali", year, rnd)

        name_path = _session_cache_path(
            "quali",
            year,
            normalize_name(
                normalise_location(event.get("Location", ""))
            ),
        )

        # Use whichever qualifying cache already exists.
        base_path = next(
            (p for p in [round_path, name_path] if os.path.exists(p)),
            None,
        )

        if base_path is None:
            print("    No existing qualifying cache found; skipping.")
            return False

        base_df = pd.read_pickle(base_path)
        updated_count = 0

        for alias in aliases:
            if not alias:
                continue

            path = _session_cache_path("quali", year, alias)
            df = (
                pd.read_pickle(path)
                if os.path.exists(path)
                else base_df.copy()
            )

            if (
                df["driver"].duplicated().any()
                or set(df["driver"]) != set(grid_map)
            ):
                print(f"    Driver mismatch: {alias}; skipping.")
                continue

            df = df.copy()
            df["grid_position"] = (
                df["driver"].map(grid_map).astype(int)
            )
            df["grid_source"] = "fastf1_race"
            df.attrs["post_race_verified"] = True

            df.to_pickle(path)
            updated_count += 1

        print(f"    Post-race grid synced to {updated_count} cache(s).")
        return updated_count > 0

    except Exception as exc:
        print(f"    Post-race grid sync failed: {exc}")
        return False


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
            _sync_postrace_grid(year, rnd)
            print(f"    Qualifying + race grid ({time.time() - t:.1f}s)")
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
