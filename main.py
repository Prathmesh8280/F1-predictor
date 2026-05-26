import argparse
import os
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from src.predictor import run
from src.data_loader import load_actual_results

# F1 team colours
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
    "Cadillac": "#C8A000",
    "Audi": "#BB0000",
}
DEFAULT_COLOR = "#888888"
PODIUM_COLORS = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}

BG_DARK  = "#0d0d1a"
BG_PANEL = "#13132b"


def _team_color(team: str) -> str:
    for key, color in TEAM_COLORS.items():
        if key.lower() in team.lower():
            return color
    return DEFAULT_COLOR


def _bezier_curve(y0: float, y1: float, x0: float, x1: float, n: int = 80):
    """Cubic bezier S-curve that departs and arrives horizontally."""
    t   = np.linspace(0, 1, n)
    mid = (x0 + x1) / 2
    bx  = (1-t)**3*x0 + 3*(1-t)**2*t*mid + 3*(1-t)*t**2*mid + t**3*x1
    by  = (1-t)**3*y0 + 3*(1-t)**2*t*y0  + 3*(1-t)*t**2*y1  + t**3*y1
    return bx.tolist(), by.tolist()


def plot_results(results, race: str, year: int, mae: float, actual_df=None):
    """Interactive slope chart: GRID → PREDICTED (→ ACTUAL if race is done).

    Bezier S-curves, team-coloured driver names, podium glow, hover tooltips.
    Saves as a standalone HTML file and opens in the browser.
    """
    n = len(results)
    by_grid = results.sort_values("grid_position").reset_index(drop=True)
    by_pred = results.sort_values("predicted_rank").reset_index(drop=True)

    has_actual = actual_df is not None and not actual_df.empty

    # Merge actual positions into results if available
    if has_actual:
        results = results.merge(actual_df, on="driver", how="left")
        by_pred = results.sort_values("predicted_rank").reset_index(drop=True)

    # Column x-positions depend on whether we have 2 or 3 columns
    if has_actual:
        x_grid, x_pred, x_actual = 0.12, 0.5, 0.88
    else:
        x_grid, x_pred, x_actual = 0.25, 0.75, None

    fig = go.Figure()

    # ── Row banding across the full channel ──────────────────────────────────
    x_left  = x_grid
    x_right = x_actual if has_actual else x_pred
    for pos in range(1, n + 1):
        fig.add_shape(
            type="rect", xref="x", yref="y",
            x0=x_left, x1=x_right, y0=pos - 0.5, y1=pos + 0.5,
            fillcolor="rgba(255,255,255,0.03)" if pos % 2 == 0 else "rgba(0,0,0,0)",
            line=dict(width=0), layer="below",
        )

    # ── Podium highlights on the GRID→PREDICTED channel ──────────────────────
    for pos, fill, border in [
        (1, "rgba(255,215,0,0.18)",   "rgba(255,215,0,0.5)"),
        (2, "rgba(192,192,192,0.12)", "rgba(192,192,192,0.35)"),
        (3, "rgba(205,127,50,0.12)",  "rgba(205,127,50,0.35)"),
    ]:
        fig.add_shape(
            type="rect", xref="x", yref="y",
            x0=x_grid, x1=x_pred, y0=pos - 0.48, y1=pos + 0.48,
            fillcolor=fill,
            line=dict(color=border, width=1),
            layer="below",
        )

    # ── GRID → PREDICTED bezier lines ────────────────────────────────────────
    seen_teams: dict = {}
    for _, row in results.iterrows():
        grid      = int(row["grid_position"])
        pred      = int(row["predicted_rank"])
        delta     = grid - pred
        color     = _team_color(row["team"])
        team      = row["team"]
        is_podium = pred <= 3

        delta_str = f"+{delta} ▲" if delta > 0 else (f"{delta} ▼" if delta < 0 else "no change")
        hover = (
            f"<b style='font-size:14px'>{row['driver']}</b><br>"
            f"<span style='color:#aaaaaa'>{team}</span><br>"
            f"Grid P{grid}  →  Predicted P{pred}<br>"
            f"<b>{delta_str}</b>"
        )

        first_for_team = team not in seen_teams
        seen_teams[team] = color
        bx, by = _bezier_curve(grid, pred, x_grid, x_pred)

        if is_podium:
            fig.add_trace(go.Scatter(
                x=bx, y=by, mode="lines",
                line=dict(color=color, width=12), opacity=0.15,
                hoverinfo="skip", showlegend=False, legendgroup=team,
            ))

        fig.add_trace(go.Scatter(
            x=bx, y=by, mode="lines",
            name=team, legendgroup=team,
            showlegend=first_for_team,
            line=dict(color=color, width=3.0 if is_podium else 1.6),
            opacity=1.0 if is_podium else 0.72,
            hoverinfo="text", hovertext=hover,
        ))

        fig.add_trace(go.Scatter(
            x=[x_grid, x_pred], y=[grid, pred], mode="markers",
            marker=dict(
                color=color, size=11 if is_podium else 7, symbol="circle",
                line=dict(color="white", width=1.5 if is_podium else 0.8),
            ),
            hoverinfo="skip", showlegend=False, legendgroup=team,
        ))

    # Build once — used by both the bezier lines and the right-side labels
    actual_lookup = dict(zip(actual_df["driver"], actual_df["actual_position"])) if has_actual else {}

    # ── PREDICTED → ACTUAL bezier lines (if race finished) ───────────────────
    if has_actual:
        for _, row in results.iterrows():
            pred   = int(row["predicted_rank"])
            actual = actual_lookup.get(row["driver"])
            if actual is None:
                continue
            actual = int(actual)
            color  = _team_color(row["team"])
            error  = abs(pred - actual)

            # Line color: green if within 2, amber if 3-4, red if 5+
            acc_color = "#44ee88" if error <= 2 else ("#ffaa00" if error <= 4 else "#ff5555")

            hover_actual = (
                f"<b style='font-size:14px'>{row['driver']}</b><br>"
                f"<span style='color:#aaaaaa'>{row['team']}</span><br>"
                f"Predicted P{pred}  →  Actual P{actual}<br>"
                f"<b>Error: {error} position{'s' if error != 1 else ''}</b>"
            )

            bx, by = _bezier_curve(pred, actual, x_pred, x_actual)
            fig.add_trace(go.Scatter(
                x=bx, y=by, mode="lines",
                line=dict(color=acc_color, width=1.8, dash="dot"),
                opacity=0.85,
                hoverinfo="text", hovertext=hover_actual,
                showlegend=False, legendgroup=row["team"],
            ))

            fig.add_trace(go.Scatter(
                x=[x_actual], y=[actual], mode="markers",
                marker=dict(
                    color=acc_color, size=9 if actual <= 3 else 6,
                    symbol="circle",
                    line=dict(color="white", width=1),
                ),
                hoverinfo="skip", showlegend=False,
            ))

    # ── Left labels: grid order ───────────────────────────────────────────────
    for _, row in by_grid.iterrows():
        grid  = int(row["grid_position"])
        color = _team_color(row["team"])
        fig.add_annotation(
            x=x_grid, y=grid,
            text=f"<span style='color:#888888'>P{grid:>2}</span>  <b><span style='color:{color}'>{row['driver']}</span></b>",
            xanchor="right", yanchor="middle", showarrow=False,
            font=dict(size=12, family="'Courier New', monospace"), xshift=-16,
        )

    # ── Middle labels: predicted order ───────────────────────────────────────
    for _, row in by_pred.iterrows():
        pred  = int(row["predicted_rank"])
        grid  = int(row["grid_position"])
        delta = grid - pred
        color = _team_color(row["team"])

        pos_col = PODIUM_COLORS.get(pred, "#dddddd")
        d_col   = "#44ee88" if delta > 0 else ("#ff5555" if delta < 0 else "#555577")
        d_sym   = f"▲{delta}" if delta > 0 else (f"▼{abs(delta)}" if delta < 0 else "—")

        if has_actual:
            # When there's an actual column, predicted labels sit above/below the dot
            fig.add_annotation(
                x=x_pred, y=pred,
                text=(
                    f"<b><span style='color:{pos_col}'>P{pred}</span></b>"
                    f" <b><span style='color:{color}'>{row['driver']}</span></b>"
                    f" <span style='color:{d_col}'>{d_sym}</span>"
                ),
                xanchor="center", yanchor="bottom", showarrow=False,
                font=dict(size=10, family="'Courier New', monospace"), yshift=8,
            )
        else:
            fig.add_annotation(
                x=x_pred, y=pred,
                text=(
                    f"<b><span style='color:{pos_col}'>P{pred}</span></b>"
                    f"  <b><span style='color:{color}'>{row['driver']}</span></b>"
                    f"  <span style='color:{d_col}'>{d_sym}</span>"
                ),
                xanchor="left", yanchor="middle", showarrow=False,
                font=dict(size=12, family="'Courier New', monospace"), xshift=16,
            )

    # ── Right labels: actual order ────────────────────────────────────────────
    if has_actual:
        driver_to_team = dict(zip(results["driver"], results["team"]))
        by_actual = actual_df.sort_values("actual_position").reset_index(drop=True)

        for _, row in by_actual.iterrows():
            actual = int(row["actual_position"])
            driver = row["driver"]
            team   = driver_to_team.get(driver, "")
            color  = _team_color(team)
            pos_col = PODIUM_COLORS.get(actual, "#dddddd")

            # Find predicted position for this driver
            pred_row = results[results["driver"] == driver]
            pred = int(pred_row["predicted_rank"].iloc[0]) if not pred_row.empty else actual
            error = pred - actual  # positive = predicted too low (driver did better)
            e_col = "#44ee88" if abs(error) <= 2 else ("#ffaa00" if abs(error) <= 4 else "#ff5555")
            e_sym = f"▲{abs(error)}" if error > 0 else (f"▼{abs(error)}" if error < 0 else "—")

            fig.add_annotation(
                x=x_actual, y=actual,
                text=(
                    f"<b><span style='color:{pos_col}'>P{actual}</span></b>"
                    f"  <b><span style='color:{color}'>{driver}</span></b>"
                    f"  <span style='color:{e_col}'>{e_sym}</span>"
                ),
                xanchor="left", yanchor="middle", showarrow=False,
                font=dict(size=12, family="'Courier New', monospace"), xshift=16,
            )

    # ── Column headers ────────────────────────────────────────────────────────
    headers = [(x_grid, "GRID"), (x_pred, "PREDICTED")]
    if has_actual:
        headers.append((x_actual, "ACTUAL"))
    for x, label in headers:
        fig.add_annotation(
            x=x, y=0.1, text=f"<b>{label}</b>",
            xanchor="center", yanchor="bottom", showarrow=False,
            font=dict(color="#666688", size=13, family="Arial"),
        )

    # ── Layout ────────────────────────────────────────────────────────────────
    subtitle = f"Model MAE: ±{mae:.2f} positions  ·  <span style='color:#44ee88'>▲ gained</span>  ·  <span style='color:#ff5555'>▼ lost</span>"
    if has_actual:
        subtitle += "  ·  Dotted lines = predicted vs actual error"

    fig.update_layout(
        title=dict(
            text=(
                f"F1 Predictor — {year} {race} Grand Prix"
                f"<br><sup>{subtitle}</sup>"
            ),
            x=0.5,
            font=dict(color="white", size=22, family="Arial Black, Arial"),
        ),
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_PANEL,
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[n + 0.7, 0.1], autorange=False),
        legend=dict(
            font=dict(color="white", size=11),
            bgcolor="rgba(13,13,26,0.85)",
            bordercolor="#2a2a4a",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=-0.07,
            xanchor="center",
            x=0.5,
            itemclick="toggleothers",
            itemdoubleclick="toggle",
        ),
        height=max(680, n * 38),
        margin=dict(l=190, r=230, t=100, b=120),
        hoverlabel=dict(
            bgcolor="#12122a",
            font=dict(color="white", size=12, family="Arial"),
            bordercolor="#4444aa",
        ),
    )

    chart_path = os.path.join("data", f"prediction_{year}_{race.replace(' ', '_')}.html")
    os.makedirs("data", exist_ok=True)
    fig.write_html(chart_path, include_plotlyjs="cdn")
    print(f"  Chart saved to: {chart_path}")

    fig.show()


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
        results, mae = run(
            race=args.race,
            year=args.year,
            train_years=tuple(args.train_years),
            force_refresh=args.refresh,
        )
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  Predicted Finish Order — {args.year} {args.race} GP")
    print(f"  Model MAE: ±{mae:.2f} positions")
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

    plot_results(results, args.race, args.year, mae, actual_df=actual_df)


if __name__ == "__main__":
    main()
