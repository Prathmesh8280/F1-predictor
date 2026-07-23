"""Walk-forward backtest + blend-weight tuning for the two-stage F1 predictor.

Every metric here is OUT-OF-SAMPLE. For each target race, in chronological
order, we train only on data available before that race:

    Stage 1 (circuit baseline) ← all *prior seasons*
    Stage 2 (current pace)     ← the same season's *earlier rounds*

then predict the race and compare to the actual finishing order. This is the
honest replacement for the in-sample MAE the pipeline used to report.

All comparisons are done in rank space (1..K over the drivers common to both
the prediction and the result), which neutralises the DNF = last-place
inflation in raw finish positions and puts the model and the grid baseline on
the same footing.

Because the blend weight only scales the final combination of the two stages'
predictions, we fit each race ONCE, cache the raw Stage 1 / Stage 2 outputs,
and re-score every candidate alpha cheaply — no re-training per alpha.

Run:
    python -m src.backtest                  # evaluate at the current BLEND_ALPHA
    python -m src.backtest --tune           # sweep alpha and report the best
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src import model as mdl
from src.data_loader import load_history, load_qualifying, load_practice_pace, normalise_location
from src.predictor import build_circuit_model, predict_components

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RESULTS_CSV = os.path.join(DATA_DIR, "backtest_results.csv")
SUMMARY_JSON = os.path.join(DATA_DIR, "backtest_summary.json")
TUNING_CSV = os.path.join(DATA_DIR, "alpha_tuning.csv")

# A race needs at least this many drivers in common between prediction and
# result before its ranking metrics are meaningful.
MIN_DRIVERS = 5


def _preload_sessions(history: pd.DataFrame, target_years, force_refresh: bool = False) -> tuple:
    """Fetch qualifying + practice pace for every round of the target years.

    Returns ({(year, round): quali_df}, {(year, round): practice_df}). The
    earliest loaded season is never a target (Stage 1 needs a prior season),
    so we skip it here and avoid the download.
    """
    all_years = sorted(history["year"].unique())
    quali_cache: dict = {}
    practice_cache: dict = {}

    for year in all_years:
        if year not in target_years:
            continue
        rounds = sorted(history[history["year"] == year]["round"].unique())
        for r in rounds:
            try:
                quali_cache[(year, r)] = load_qualifying(year, int(r), force_refresh=force_refresh)
            except Exception as e:
                print(f"  No qualifying for {year} R{r}: {e}")
            try:
                practice_cache[(year, r)] = load_practice_pace(year, int(r), force_refresh=force_refresh)
            except Exception as e:
                print(f"  No FP2 for {year} R{r}: {e}")

    return quali_cache, practice_cache


def _collect_components(history: pd.DataFrame, quali_cache: dict, practice_cache: dict,
                        target_years, stage1_circuit_only=True) -> tuple:
    """Walk forward once, fitting each race and caching its raw stage outputs.

    features/estimator configure Stage 2 (defaults = production).
    stage1_circuit_only trains Stage 1 on only the target track's history
    (production default; matches run()). Set False to pool all circuits.
    Returns (records, skipped). Each record is a dict with meta fields plus a
    'frame' DataFrame holding per-driver columns: grid_position, pred1, pred2
    (NaN when no pace model), finish_position — over the common driver set.
    """
    targets = (
        history[history["year"].isin(target_years)][["year", "round", "event_name", "location"]]
        .drop_duplicates()
        .sort_values(["year", "round"])
        .itertuples(index=False)
    )

    records, skipped = [], []
    for tgt in targets:
        year, rnd, event, location = int(tgt.year), int(tgt.round), tgt.event_name, normalise_location(tgt.location)
        label = f"{year} R{rnd:>2} {event}"

        quali_df = quali_cache.get((year, rnd))
        if quali_df is None or quali_df.empty:
            skipped.append((label, "no qualifying data"))
            continue

        circuit_history = history[history["year"] < year]
        season_train    = history[(history["year"] == year) & (history["round"] < rnd)]

        stage1_model, circuit_map = build_circuit_model(
            circuit_history, verbose=False,
            only_location=location if stage1_circuit_only else None,
        )

        x_circuit, pred1, pred2 = predict_components(
            stage1_model, circuit_map,
            quali_df, practice_cache.get((year, rnd)), season_train, location,
        )

        frame = x_circuit[["driver", "grid_position"]].copy()
        frame["pred1"] = pred1
        frame["pred2"] = pred2 if pred2 is not None else np.nan

        actual = history[(history["year"] == year) & (history["round"] == rnd)][["driver", "finish_position", "finished"]]
        merged = frame.merge(actual, on="driver", how="inner")
        if len(merged) < MIN_DRIVERS:
            skipped.append((label, f"only {len(merged)} drivers matched"))
            continue

        records.append({
            "year": year, "round": rnd, "event_name": event, "label": label,
            "stage2_used": pred2 is not None,  # True when FP2 pace rank was used
            "frame": merged,
        })

    return records, skipped


def _blended_positions(frame: pd.DataFrame, alpha: float) -> np.ndarray:
    """Blend Stage 1 circuit-adjusted rank with Stage 2 rank.

    pred1 = Stage 1 delta (finish - grid). circuit_rank = rank(grid + delta1).
    pred2 = Stage 2 composite rank (championship form + FP2 pace).
    score = alpha * circuit_rank + (1-alpha) * stage2_rank.
    alpha=1 → pure Stage 1; alpha=0 → pure Stage 2.
    """
    grid = frame["grid_position"].values
    delta1 = frame["pred1"].values
    circuit_adjusted = grid + delta1
    circuit_rank = pd.Series(circuit_adjusted).rank(method="min").values

    if frame["pred2"].notna().all():
        stage2_rank = frame["pred2"].values
        return alpha * circuit_rank + (1 - alpha) * stage2_rank
    return circuit_rank


def _subset_metrics(sub: pd.DataFrame, positions) -> dict:
    """Rank-space metrics over one driver subset (model vs grid baseline)."""
    sub = sub.reset_index(drop=True)
    pred = pd.Series(np.asarray(positions), index=sub.index).rank(method="first")
    actual = sub["finish_position"].rank(method="first")
    grid = sub["grid_position"].rank(method="first")

    k = len(sub)
    top = lambda s, n: set(s.nsmallest(min(n, k)).index)
    model_top3, actual_top3 = top(pred, 3), top(actual, 3)
    model_top10, actual_top10 = top(pred, 10), top(actual, 10)

    return {
        "model_mae": float(np.abs(pred - actual).mean()),
        "baseline_mae": float(np.abs(grid - actual).mean()),
        "model_spearman": float(spearmanr(pred, actual).correlation) if k > 1 else float("nan"),
        "baseline_spearman": float(spearmanr(grid, actual).correlation) if k > 1 else float("nan"),
        "podium_hit": len(model_top3 & actual_top3) / min(3, k),
        "top10_hit": len(model_top10 & actual_top10) / min(10, k),
        # How far predictions deviate from grid order (0 = identical to grid).
        # A measure of how "bold" the model is, independent of accuracy.
        "movement": float(np.abs(pred - grid).mean()),
    }


def _race_metrics(frame: pd.DataFrame, alpha: float) -> dict:
    """Rank-space metrics for one race: all drivers, plus finishers-only.

    Includes delta accuracy metrics (the primary measure of model quality):
      delta_mae        — MAE of (predicted_delta − actual_delta). Baseline is
                         predicting delta=0 for everyone (grid order).
      delta_baseline   — mean |actual_delta|, i.e. what delta_mae=0 prediction
                         requires us to beat.
      directional_acc  — among drivers who moved 3+ places, fraction where we
                         correctly predicted the direction (gain vs loss).
    """
    frame = frame.reset_index(drop=True)
    positions = np.asarray(_blended_positions(frame, alpha))

    overall = _subset_metrics(frame, positions)
    overall["n_drivers"] = len(frame)

    # Delta accuracy metrics (new primary evaluation)
    actual_delta    = frame["finish_position"].values - frame["grid_position"].values
    predicted_delta = positions - frame["grid_position"].values
    overall["delta_mae"]      = float(np.abs(actual_delta - predicted_delta).mean())
    overall["delta_baseline"] = float(np.abs(actual_delta).mean())

    movers = np.abs(actual_delta) >= 3
    if movers.sum() >= 3:
        overall["directional_acc"] = float(
            (np.sign(actual_delta[movers]) == np.sign(predicted_delta[movers])).mean()
        )
    else:
        overall["directional_acc"] = float("nan")

    fin_mask = frame["finished"].fillna(True).to_numpy(dtype=bool)
    if fin_mask.sum() >= MIN_DRIVERS:
        fin = _subset_metrics(frame[fin_mask], positions[fin_mask])
        overall.update({
            "model_mae_fin": fin["model_mae"],
            "baseline_mae_fin": fin["baseline_mae"],
            "model_spearman_fin": fin["model_spearman"],
            "n_finishers": int(fin_mask.sum()),
        })
    return overall


def _aggregate(records: list, alpha: float) -> dict:
    """Macro-average the per-race metrics across all records at one alpha."""
    df = pd.DataFrame([_race_metrics(rec["frame"], alpha) for rec in records])
    mean = lambda col: float(df[col].mean()) if col in df else float("nan")
    return {
        "n_races": int(len(df)),
        "model_mae": mean("model_mae"),
        "baseline_mae": mean("baseline_mae"),
        "model_spearman": mean("model_spearman"),
        "baseline_spearman": mean("baseline_spearman"),
        "podium_hit": mean("podium_hit"),
        "top10_hit": mean("top10_hit"),
        "model_mae_fin": mean("model_mae_fin"),
        "baseline_mae_fin": mean("baseline_mae_fin"),
        "model_spearman_fin": mean("model_spearman_fin"),
        "movement": mean("movement"),
        "delta_mae": mean("delta_mae"),
        "delta_baseline": mean("delta_baseline"),
        "directional_acc": mean("directional_acc"),
    }


def load_and_preload(years, force_refresh, eval_years=None):
    """Load history + qualifying/practice sessions once.

    eval_years restricts which seasons are *evaluated* (default: every season
    after the earliest). Earlier seasons are still loaded for Stage 1 training.
    Returns (years, history, quali_cache, practice_cache, target_years).
    """
    years = tuple(sorted(years))
    print(f"\n{'='*60}\n  Walk-forward backtest — seasons {list(years)}\n{'='*60}")

    history = load_history(train_years=years, force_refresh=force_refresh)
    earliest = min(history["year"].unique())
    target_years = [y for y in years if y > earliest]
    if eval_years is not None:
        target_years = [y for y in target_years if y in set(eval_years)]
    if not target_years:
        raise RuntimeError(
            f"No evaluable seasons; loaded {sorted(history['year'].unique())}, "
            f"eval_years={eval_years}. Need at least one season after the earliest."
        )
    training_only = [y for y in years if y not in target_years]
    print(f"  Training-only (Stage 1): {training_only}   |   evaluating: {target_years}\n")

    print("Pre-loading qualifying + practice sessions (cached after first run)...")
    quali_cache, practice_cache = _preload_sessions(history, target_years, force_refresh=force_refresh)
    return years, history, quali_cache, practice_cache, target_years


def _prepare(years, force_refresh, eval_years=None):
    """load_and_preload + collect per-race components for one Stage 2 config."""
    years, history, quali_cache, practice_cache, target_years = load_and_preload(
        years, force_refresh, eval_years=eval_years)
    records, skipped = _collect_components(
        history, quali_cache, practice_cache, target_years,
    )
    if skipped:
        print(f"\nSkipped {len(skipped)} race(s):")
        for label, why in skipped:
            print(f"  - {label}: {why}")
    if not records:
        raise RuntimeError("No races could be evaluated — check data availability.")
    return years, records


def run_backtest(years=(2024, 2025, 2026), force_refresh=False, alpha=None, eval_years=None) -> dict:
    """Evaluate the predictor at a fixed blend weight (default BLEND_ALPHA)."""
    years, records = _prepare(years, force_refresh, eval_years=eval_years)
    alpha = mdl.BLEND_ALPHA if alpha is None else alpha

    # Per-race detail table.
    rows = []
    for rec in records:
        m = _race_metrics(rec["frame"], alpha)
        m.update({"year": rec["year"], "round": rec["round"], "event_name": rec["event_name"],
                  "stage2_used": rec["stage2_used"]})
        rows.append(m)
        flag = "" if rec["stage2_used"] else "  (Stage 1 only - no form yet)"
        print(f"  {rec['label']:<34}  MAE {m['model_mae']:.2f}  vs grid {m['baseline_mae']:.2f}{flag}")

    os.makedirs(DATA_DIR, exist_ok=True)
    pd.DataFrame(rows).to_csv(RESULTS_CSV, index=False)

    overall = _aggregate(records, alpha)
    stage2 = [r for r in records if r["stage2_used"]]
    summary = {"years": list(years), "alpha": alpha, **overall, "n_races_stage2": len(stage2)}
    if stage2:
        summary["stage2_only"] = _aggregate(stage2, alpha)
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    _print_summary(overall, summary.get("stage2_only"), alpha)
    return summary


def tune_alpha(years=(2024, 2025, 2026), force_refresh=False, step=0.05, eval_years=None) -> dict:
    """Sweep the circuit-vs-pace blend weight and report the best by OOS MAE."""
    years, records = _prepare(years, force_refresh, eval_years=eval_years)

    alphas = [round(a, 2) for a in np.arange(0.0, 1.0 + 1e-9, step)]
    sweep = []
    for a in alphas:
        agg = _aggregate(records, a)
        agg["alpha"] = a
        sweep.append(agg)
    sweep_df = pd.DataFrame(sweep)

    os.makedirs(DATA_DIR, exist_ok=True)
    sweep_df.to_csv(TUNING_CSV, index=False)

    best_spear = sweep_df.loc[sweep_df["model_spearman_fin"].idxmax()]
    best_podium = sweep_df.loc[sweep_df["podium_hit"].idxmax()]
    best_dir = sweep_df.loc[sweep_df["directional_acc"].idxmax()]
    baseline_spear = sweep_df["baseline_spearman"].iloc[0]

    print(f"\n{'='*72}\n  ALPHA SWEEP  ({int(best_spear['n_races'])} races)\n{'='*72}")
    print(f"  grid baseline: Spearman(fin) {baseline_spear:.3f}")
    print(f"  (alpha = weight on grid; lower alpha = more pace-dominant)")
    print(f"  {'alpha':>6}{'Spear(fin)':>12}{'Podium%':>9}{'Dir.acc':>9}{'move':>7}{'MAE(fin)':>10}")
    print(f"  {'-'*57}")
    for _, r in sweep_df.iterrows():
        marks = []
        if r["alpha"] == best_spear["alpha"]: marks.append("Spear")
        if r["alpha"] == best_podium["alpha"]: marks.append("Podium")
        if r["alpha"] == best_dir["alpha"]: marks.append("Dir")
        mark = f"  <- best({','.join(marks)})" if marks else ""
        b = "*" if r["model_spearman_fin"] > baseline_spear else " "
        print(f"  {r['alpha']:>6.2f}{r['model_spearman_fin']:>11.3f}{b}{r['podium_hit']:>9.1%}"
              f"{r['directional_acc']:>9.1%}{r['movement']:>7.2f}{r['model_mae_fin']:>10.3f}{mark}")
    print(f"  {'-'*57}\n  ( * = beats grid Spearman baseline )")

    print(f"\n  Best Spearman(fin) : alpha {best_spear['alpha']:.2f}  ->  {best_spear['model_spearman_fin']:.3f} "
          f"(grid {baseline_spear:.3f})")
    print(f"  Best Podium hit    : alpha {best_podium['alpha']:.2f}  ->  {best_podium['podium_hit']:.1%}")
    print(f"  Best Directional   : alpha {best_dir['alpha']:.2f}  ->  {best_dir['directional_acc']:.1%}")
    print(f"\n  Sweep table : {TUNING_CSV}\n")
    return {
        "best_alpha": float(best_spear["alpha"]),
        "best_spearman": float(best_spear["model_spearman_fin"]),
        "best_alpha_podium": float(best_podium["alpha"]),
        "best_podium": float(best_podium["podium_hit"]),
        "baseline_spearman": float(baseline_spear),
    }


def _print_summary(overall: dict, stage2_only: dict, alpha: float) -> None:
    print(f"\n{'='*60}\n  OUT-OF-SAMPLE RESULTS  ({overall['n_races']} races, alpha={alpha:.2f})\n{'='*60}")
    print(f"  (alpha={alpha:.2f}: {(1-alpha)*100:.0f}% pace / {alpha*100:.0f}% grid)")
    print(f"\n  {'metric':<26}{'model':>10}{'grid baseline':>16}")
    print(f"  {'-'*52}")

    spear_edge = overall["model_spearman_fin"] - overall["baseline_spearman"]
    spear_verdict = "beats" if spear_edge > 0 else "trails"
    print(f"  {'Spearman (finishers)':<26}{overall['model_spearman_fin']:>10.3f}{overall['baseline_spearman']:>16.3f}")
    print(f"  {'Spearman (all)':<26}{overall['model_spearman']:>10.3f}{overall['baseline_spearman']:>16.3f}")
    print(f"  {'Podium hit rate':<26}{overall['podium_hit']:>10.1%}{'':>16}")
    print(f"  {'Top-10 hit rate':<26}{overall['top10_hit']:>10.1%}{'':>16}")

    dir_acc = overall.get("directional_acc", float("nan"))
    if not (isinstance(dir_acc, float) and dir_acc != dir_acc):
        print(f"  {'Directional acc. (>=3 pos)':<26}{dir_acc:>10.1%}{'':>16}")

    print(f"  {'-'*52}")
    print(f"  Model {spear_verdict} grid Spearman by {abs(spear_edge):.3f} (finishers).")

    print(f"\n  MAE (for reference only — not the optimization target):")
    print(f"  {'MAE all drivers':<26}{overall['model_mae']:>10.3f}{overall['baseline_mae']:>16.3f}")
    print(f"  {'MAE finishers only':<26}{overall['model_mae_fin']:>10.3f}{overall['baseline_mae_fin']:>16.3f}")

    if stage2_only:
        print(f"\n  Pace-active races ({stage2_only['n_races']}): "
              f"Spearman {stage2_only['model_spearman_fin']:.3f}")
    print(f"\n  Per-race detail : {RESULTS_CSV}")
    print(f"  Summary         : {SUMMARY_JSON}\n")


def main():
    parser = argparse.ArgumentParser(description="Walk-forward backtest for the F1 predictor.")
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025, 2026],
                        help="Seasons to load. The earliest is training-only; the rest are evaluable.")
    parser.add_argument("--eval-years", nargs="+", type=int, default=None,
                        help="Restrict which seasons are evaluated (e.g. 2026). Others still train Stage 1.")
    parser.add_argument("--tune", action="store_true", help="Sweep the blend weight instead of a single run.")
    parser.add_argument("--step", type=float, default=0.05, help="Alpha step size for --tune (default 0.05).")
    parser.add_argument("--refresh", action="store_true", help="Force re-download of cached data.")
    args = parser.parse_args()

    eval_years = tuple(args.eval_years) if args.eval_years else None
    if args.tune:
        tune_alpha(years=tuple(args.years), force_refresh=args.refresh, step=args.step, eval_years=eval_years)
    else:
        run_backtest(years=tuple(args.years), force_refresh=args.refresh, eval_years=eval_years)


if __name__ == "__main__":
    main()
