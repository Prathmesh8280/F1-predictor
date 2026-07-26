import logging
import os
from datetime import datetime, timezone
import fastf1
import numpy as np
import pandas as pd

# Suppress FastF1's verbose INFO chatter — we print our own progress messages.
# WARNING and above (accuracy checks, tyre corrections, etc.) stay visible.
logging.getLogger("fastf1").setLevel(logging.WARNING)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# FastF1 returns different Location strings for the same circuit across API
# versions / seasons. Normalise to a single canonical name so circuit-map
# lookups work regardless of which year's data we are comparing.
_LOCATION_CANONICAL: dict[str, str] = {
    "Monte Carlo": "Monaco",
    "Miami Gardens": "Miami",
    "Sakhir": "Bahrain",
    "Yas Island": "Abu Dhabi",
    "Marina Bay": "Singapore",
    "Lusail": "Qatar",
    "Jeddah": "Saudi Arabia",
    "Melbourne": "Australia",
    "Shanghai": "China",
    "Suzuka": "Japan",
    "Spielberg": "Austria",
    "Silverstone": "Britain",
    "Budapest": "Hungary",
    "Spa-Francorchamps": "Belgium",
    "Zandvoort": "Netherlands",
    "Monza": "Italy",
    "Mexico City": "Mexico",
    "Interlagos": "Sao Paulo",
    "Las Vegas": "Las Vegas",
    "Austin": "Austin",
}


def normalise_location(loc: str) -> str:
    """Map FastF1 location strings to canonical circuit names."""
    return _LOCATION_CANONICAL.get(loc, loc)


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)


def _history_cache_path(train_years) -> str:
    key = "_".join(str(y) for y in sorted(train_years))
    return os.path.join(CACHE_DIR, f"history_{key}_v3.pkl")


def _session_cache_path(prefix: str, year: int, race) -> str:
    race_key = str(race).lower().replace(" ", "_").replace("/", "_")
    return os.path.join(CACHE_DIR, f"{prefix}_{year}_{race_key}.pkl")


def load_history(train_years=(2024, 2025), force_refresh=False) -> pd.DataFrame:
    """Load race results for all completed races in the given years."""
    _ensure_cache_dir()
    cache_path = _history_cache_path(train_years)

    if not force_refresh and os.path.exists(cache_path):
        print("Loading historical data from cache...")
        df = pd.read_pickle(cache_path)
        df["location"] = df["location"].map(normalise_location)
        return df

    print(f"Downloading historical race data for seasons: {list(train_years)}")
    rows = []
    now = datetime.now(timezone.utc)

    for year in train_years:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        completed = schedule[
            (schedule["EventFormat"] != "testing")
            & (pd.to_datetime(schedule["EventDate"], utc=True) < now)
        ]

        for _, event in completed.iterrows():
            round_num = event["RoundNumber"]
            event_name = event["EventName"]
            location = normalise_location(event.get("Location", event_name))

            try:
                session = fastf1.get_session(year, round_num, "R")
                session.load(laps=False, telemetry=False, weather=False, messages=False)
            except Exception as e:
                print(f"  Skipping {year} R{round_num} ({event_name}): {e}")
                continue

            results = session.results
            if results is None or results.empty:
                continue

            for _, driver in results.iterrows():
                position = driver.get("Position")
                grid = driver.get("GridPosition")

                if pd.isna(position):
                    position = len(results) + 1
                else:
                    position = int(position)

                # Classified finishers have Status "Finished" or "+N Lap(s)";
                # anything else (Accident, Engine, Retired, DNS, DSQ...) is a
                # non-finish. Used for DNF-aware evaluation.
                status = str(driver.get("Status", ""))
                finished = (status == "Finished") or ("Lap" in status)

                rows.append({
                    "year": year,
                    "round": round_num,
                    "event_name": event_name,
                    "location": location,
                    "driver": driver.get("Abbreviation", ""),
                    "team": driver.get("TeamName", ""),
                    "grid_position": int(grid) if not pd.isna(grid) else 20,
                    "finish_position": position,
                    "finished": finished,
                })
            print(f"  Loaded {year} R{round_num}: {event_name}")

    df = pd.DataFrame(rows)
    df.to_pickle(cache_path)
    print(f"Saved {len(df)} driver-race rows to cache.")
    return df


def fetch_race_grid(year: int, race) -> dict:
    """Return {driver_abbr: grid_position} from the race session, or {} if unavailable.

    Grid positions from the race session reflect penalties applied after qualifying
    (gearbox, engine, pit-lane starts). Returns empty dict when the race hasn't
    happened yet — callers fall back to qualifying order in that case.
    FastF1 caches sessions locally, so this is fast after the first load.
    """
    try:
        race_session = fastf1.get_session(year, race, "R")
        race_session.load(laps=False, telemetry=False, weather=False, messages=False)
        res = race_session.results
        if res is None or res.empty:
            return {}
        return {
            r.get("Abbreviation", ""): int(r.get("GridPosition"))
            for _, r in res.iterrows()
            if r.get("Abbreviation", "") and not pd.isna(r.get("GridPosition"))
        }
    except Exception:
        return {}


def load_qualifying(year: int, race, force_refresh: bool = False) -> pd.DataFrame:
    """Load qualifying session — best of Q3/Q2/Q1 per driver.

    Grid positions come from the race session results, not qualifying, because
    grid penalties (e.g. gearbox, engine penalties) are applied after qualifying
    and are only reflected in the race session's GridPosition. For races that
    haven't happened yet the race session falls back gracefully to qualifying order.

    Grid positions in the returned DataFrame reflect qualifying order. Callers
    that have the race history available (predictor.run, backtest._collect_components)
    overlay the penalty-corrected grid from load_history before using it.
    """
    _ensure_cache_dir()
    cache_path = _session_cache_path("quali", year, race)

    if not force_refresh and os.path.exists(cache_path):
        return pd.read_pickle(cache_path)

    print(f"Fetching qualifying data: {year} {race}...")

    try:
        session = fastf1.get_session(year, race, "Q")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
    except Exception as e:
        raise RuntimeError(f"Could not load qualifying session for {year} {race}: {e}")

    results = session.results
    if results is None or results.empty:
        raise RuntimeError(f"No qualifying results found for {year} {race}")

    actual_grid = fetch_race_grid(year, race)

    rows = []
    for _, driver in results.iterrows():
        q_time = None
        for col in ("Q3", "Q2", "Q1"):
            val = driver.get(col)
            if val is not None and not pd.isna(val):
                try:
                    q_time = val.total_seconds()
                    break
                except AttributeError:
                    q_time = float(val)
                    break

        drv_abbr = driver.get("Abbreviation", "")

        # Prefer race-session GridPosition (includes penalties) over qualifying order.
        if drv_abbr in actual_grid:
            grid = actual_grid[drv_abbr]
        else:
            grid = driver.get("GridPosition")
            if pd.isna(grid):
                grid = driver.get("Position", 20)
            grid = int(grid) if not pd.isna(grid) else 20

        rows.append({
            "driver": drv_abbr,
            "team": driver.get("TeamName", ""),
            "qualifying_time_s": q_time,
            "grid_position": grid,
        })

    df = pd.DataFrame(rows)
    df.to_pickle(cache_path)
    return df


_FUEL_BURN_KG_PER_LAP = 2.3      # average fuel consumption per lap
_FUEL_TIME_S_PER_KG  = 0.035     # lap time penalty per kg of fuel carried


def load_practice_pace(year: int, race, force_refresh: bool = False) -> pd.DataFrame:
    """Load race pace proxy from FP2 long runs (or Sprint laps on sprint weekends).

    Applies three corrections so drivers on different compounds, fuel loads, and
    session positions are directly comparable:

      1. Fuel correction   — each lap of TyreLife the car is lighter; add back
                             the fuel advantage to normalise all laps to the
                             same (heaviest, lap-1) fuel reference.
      2. Track evolution   — rubber builds up during the session, making it
                             progressively faster; correct by normalising each
                             10-minute window to the session median.
      3. Compound norm     — subtract each compound's session median so soft /
                             medium / hard lap times are apples-to-apples.

    After correction, practice_pace_s is centred near 0: negative = faster than
    the compound-adjusted field median, positive = slower.

    Also computes a per-driver degradation_rate (s/lap from a linear fit to
    fuel-corrected compound-normalised laps vs TyreLife). Lower β = tyres last
    longer = driver gains ground in the second half of long stints.

    Returns DataFrame(driver, practice_pace_s, degradation_rate).
    """
    _ensure_cache_dir()
    cache_path = _session_cache_path("practice", year, race)
    if not force_refresh and os.path.exists(cache_path):
        return pd.read_pickle(cache_path)

    try:
        event = fastf1.get_event(year, race)
        event_format = str(event.get("EventFormat", "")).lower()
        is_sprint = "sprint" in event_format
    except Exception:
        is_sprint = False

    try:
        if is_sprint:
            print(f"  Sprint weekend — loading Sprint race laps for {year} {race}...")
            session = fastf1.get_session(year, race, "S")
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            laps = session.laps.copy()
            # Skip lap 1 (standing start noise) and require accurate timing
            laps = laps[
                laps["IsAccurate"]
                & (laps["LapNumber"] > 1)
                & laps["Compound"].isin(["SOFT", "MEDIUM", "HARD"])
            ].copy()
        else:
            print(f"  Loading FP2 long runs for {year} {race}...")
            session = fastf1.get_session(year, race, "FP2")
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            laps = session.laps.copy()
            # TyreLife >= 3 skips the warm-up laps at the start of each stint
            laps = laps[
                laps["IsAccurate"]
                & (laps["TyreLife"] >= 3)
                & laps["Compound"].isin(["SOFT", "MEDIUM", "HARD"])
            ].copy()
    except Exception as e:
        print(f"  Warning: Could not load practice/sprint data for {year} {race}: {e}")
        return pd.DataFrame(columns=["driver", "practice_pace_s", "degradation_rate"])

    if laps.empty:
        print(f"  Warning: No usable practice laps found for {year} {race}")
        return pd.DataFrame(columns=["driver", "practice_pace_s", "degradation_rate"])

    laps["lap_time_s"] = laps["LapTime"].dt.total_seconds()
    laps = laps[laps["lap_time_s"].notna() & (laps["lap_time_s"] > 60)].copy()

    if laps.empty:
        return pd.DataFrame(columns=["driver", "practice_pace_s", "degradation_rate"])

    # ── 1. Fuel correction ────────────────────────────────────────────────────
    # Add time to later laps to normalise them to the heavier (lap-1) fuel load.
    # Effect: TyreLife=8 lap gets +7 × 2.3 × 0.035 ≈ +0.56 s so a lap run on
    # lighter fuel is not artificially ranked faster than an early-stint lap.
    tyre_age = laps["TyreLife"].clip(lower=1)
    laps["fuel_corrected_s"] = (
        laps["lap_time_s"]
        + (tyre_age - 1) * _FUEL_BURN_KG_PER_LAP * _FUEL_TIME_S_PER_KG
    )

    # ── 2. Track evolution correction ────────────────────────────────────────
    # The track gets faster as rubber goes down during the session. Bin laps
    # into 10-minute windows; subtract each window's median from the session
    # median so early laps (green track) are not penalised vs late laps.
    if "Time" in laps.columns and laps["Time"].notna().any():
        session_minutes = laps["Time"].dt.total_seconds() / 60
        laps["time_bin"] = (session_minutes // 10).astype(int)
        bin_med = laps.groupby("time_bin")["fuel_corrected_s"].transform("median")
        session_med = laps["fuel_corrected_s"].median()
        laps["evo_corrected_s"] = laps["fuel_corrected_s"] - (bin_med - session_med)
    else:
        laps["evo_corrected_s"] = laps["fuel_corrected_s"]

    # ── 3. Compound normalisation ─────────────────────────────────────────────
    # Subtract each compound's session median so a driver on mediums and a
    # driver on softs are measured relative to their own compound's field, not
    # in absolute seconds (which would just re-rank by tyre choice).
    compound_med = laps.groupby("Compound")["evo_corrected_s"].transform("median")
    laps["normalized_pace_s"] = laps["evo_corrected_s"] - compound_med

    # ── Per-driver median pace ────────────────────────────────────────────────
    pace_median = (
        laps.groupby("Driver")["normalized_pace_s"]
        .median()
        .reset_index()
        .rename(columns={"Driver": "driver", "normalized_pace_s": "practice_pace_s"})
    )

    # ── Per-driver degradation rate (β, s/lap) ────────────────────────────────
    # Linear fit to fuel-corrected compound-normalised times vs TyreLife.
    # Positive β = tyres degrade (expected). Lower β = better tyre life = gains
    # in the race second half.
    fuel_compound_medians = laps.groupby("Compound")["fuel_corrected_s"].median().to_dict()
    deg_rows = []
    for driver, dlaps in laps.groupby("Driver"):
        deg_rate = float("nan")
        if len(dlaps) >= 5:
            compound = dlaps["Compound"].mode().iloc[0]
            comp_med = fuel_compound_medians.get(compound, dlaps["fuel_corrected_s"].median())
            y = dlaps["fuel_corrected_s"].values - comp_med
            x = dlaps["TyreLife"].values
            if len(set(x)) >= 3:
                deg_rate = float(np.polyfit(x, y, 1)[0])
        deg_rows.append({"driver": driver, "degradation_rate": deg_rate})

    deg_df = pd.DataFrame(deg_rows)
    result = pace_median.merge(deg_df, on="driver", how="left")

    # ── Teammate fallback for drivers with no valid laps ──────────────────────
    # When FastF1 marks all of a driver's laps as inaccurate they get no pace
    # entry. Rather than filling with worst-pace (penalises them unfairly), use
    # the teammate's pace as a proxy — same car, same weekend conditions.
    if hasattr(session, "results") and session.results is not None and not session.results.empty:
        team_map = {
            r.get("Abbreviation", ""): r.get("TeamName", "")
            for _, r in session.results.iterrows()
            if r.get("Abbreviation", "")
        }
        # Group drivers by team
        team_to_drivers: dict = {}
        for drv, team in team_map.items():
            team_to_drivers.setdefault(team, []).append(drv)

        drivers_with_pace = set(result["driver"])
        fill_rows = []
        for drv, team in team_map.items():
            if drv in drivers_with_pace or not team:
                continue
            teammates_with_pace = [
                t for t in team_to_drivers.get(team, [])
                if t != drv and t in drivers_with_pace
            ]
            if teammates_with_pace:
                teammate_pace = result[result["driver"].isin(teammates_with_pace)]["practice_pace_s"].mean()
                teammate_deg  = result[result["driver"].isin(teammates_with_pace)]["degradation_rate"].mean()
                fill_rows.append({"driver": drv, "practice_pace_s": teammate_pace, "degradation_rate": teammate_deg})
                print(f"  FP2 fallback: {drv} -> teammate pace ({', '.join(teammates_with_pace)})")

        if fill_rows:
            result = pd.concat([result, pd.DataFrame(fill_rows)], ignore_index=True)

    print(f"  Race pace loaded for {len(result)} drivers.")
    result.to_pickle(cache_path)
    return result


def load_actual_results(year: int, race: str) -> pd.DataFrame | None:
    """Try to load actual race finish positions from FastF1.

    Returns a DataFrame with columns (driver, actual_position) if the race
    has finished, or None if it hasn't happened yet or data is unavailable.
    """
    _ensure_cache_dir()
    try:
        session = fastf1.get_session(year, race, "R")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        res = session.results
        if res is None or res.empty:
            return None
        rows = []
        for _, driver in res.iterrows():
            pos = driver.get("Position")
            if pd.isna(pos):
                pos = 20
            rows.append({
                "driver": driver.get("Abbreviation", ""),
                "actual_position": int(pos),
            })
        print(f"  Actual results loaded for {year} {race}.")
        return pd.DataFrame(rows)
    except Exception:
        return None
