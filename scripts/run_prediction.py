"""Run a single race prediction from the command line and print the order.

A lightweight, headless alternative to the legacy CLI (scripts/legacy/main.py):
no chart, just the predicted finishing order — handy for quick local checks.

Usage:
  python scripts/run_prediction.py --race Italy --year 2026
  python scripts/run_prediction.py --race Madrid --year 2026 --refresh
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.predictor import run


def main():
    parser = argparse.ArgumentParser(description="Predict an F1 race finishing order.")
    parser.add_argument("--race", required=True, help='Circuit key, e.g. "Italy", "Madrid"')
    parser.add_argument("--year", required=True, type=int, help="Season, e.g. 2026")
    parser.add_argument("--refresh", action="store_true", help="Force data re-download.")
    args = parser.parse_args()

    results, stats = run(race=args.race, year=args.year, force_refresh=args.refresh)

    mae = stats.get("model_mae_fin")
    print(f"\n{'='*55}")
    print(f"  Predicted order — {args.year} {args.race}")
    if mae is not None:
        print(f"  Backtest MAE (finishers): +-{mae:.2f} positions")
    print(f"{'='*55}")
    for _, row in results.sort_values("predicted_rank").iterrows():
        print(f"  P{int(row['predicted_rank']):>2}  {row['driver']:<5}  "
              f"{row['team']:<25}  (grid P{int(row['grid_position'])})")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
