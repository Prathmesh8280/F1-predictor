"""Download raw race-result history from FastF1 for one or more seasons.

This fetches (and caches as pkl) the completed-race results that feed the
Stage 1 circuit-pattern model. Distinct from rebuild_cache.py, which also warms
per-round qualifying and practice data for the current season.

Usage:
  python scripts/download_data.py --years 2024 2025
  python scripts/download_data.py --years 2026 --refresh
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.data_loader import load_history


def main():
    parser = argparse.ArgumentParser(description="Download FastF1 race-result history by season.")
    parser.add_argument("--years", nargs="+", type=int, required=True,
                        help="Seasons to download, e.g. --years 2024 2025 2026")
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-download, ignoring existing cache.")
    args = parser.parse_args()

    for year in args.years:
        print(f"\n── Downloading {year} race history ─────────────────────────")
        t = time.time()
        df = load_history(train_years=(year,), force_refresh=args.refresh)
        print(f"   {len(df)} driver-race rows ({time.time() - t:.1f}s)")


if __name__ == "__main__":
    main()
