import argparse
import os
import sys
import pandas as pd
from src.predictor import run
from src.data_loader import load_actual_results
from src.visualize import build_chart


def main():
    parser = argparse.ArgumentParser(
        description="F1 Race Winner Predictor — fetches all data from FastF1 automatically."
    )
    parser.add_argument("--race", required=True, help='Race name, e.g. "Monaco" or "Bahrain"')
    parser.add_argument("--year", required=True, type=int, help="Race year, e.g. 2026")
    parser.add_argument(
        "--train-years",
        nargs="+",
        type=int,
        default=[2024, 2025],
        help="Historical seasons for circuit pattern model (default: 2024 2025). "
             "Current year data is always loaded separately for the pace model.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-download of historical data (ignore cache)",
    )
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  F1 Predictor: {args.year} {args.race} Grand Prix")
    print(f"  Training on seasons: {args.train_years}")
    print(f"{'='*55}\n")

    try:
        results, stats = run(
            race=args.race,
            year=args.year,
            train_years=tuple(args.train_years),
            force_refresh=args.refresh,
        )
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    mae_val = stats.get("model_mae_fin")
    mae_line = (
        f"  Backtest MAE (finishers, DNFs excluded): ±{mae_val:.2f} positions"
        if mae_val is not None
        else "  Backtest MAE: run backtest.py for out-of-sample error"
    )
    print(f"\n{'='*55}")
    print(f"  Predicted Finish Order — {args.year} {args.race} GP")
    print(mae_line)
    print(f"{'='*55}")

    for _, row in results.iterrows():
        rank = int(row["predicted_rank"])
        tag = " **" if rank <= 3 else "   "
        print(
            f"  P{rank:>2}{tag}  {row['driver']:<5}  {row['team']:<25}  "
            f"(grid P{int(row['grid_position'])})"
        )

    print(f"{'='*55}\n")

    # Try to load actual results — silently skipped if race hasn't happened yet
    print("Checking for actual race results...")
    actual_df = load_actual_results(args.year, args.race)
    if actual_df is None:
        print("  Race not yet finished — showing prediction only.")

    fig = build_chart(results, args.race, args.year, actual_df=actual_df)
    chart_path = os.path.join("data", f"prediction_{args.year}_{args.race.replace(' ', '_')}.html")
    os.makedirs("data", exist_ok=True)
    fig.write_html(chart_path, include_plotlyjs="cdn")
    print(f"  Chart saved to: {chart_path}")
    fig.show()


if __name__ == "__main__":
    main()
