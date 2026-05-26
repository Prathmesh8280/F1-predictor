import os
from datetime import datetime, timezone
import fastf1
import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)


def _history_cache_path(train_years) -> str:
    key = "_".join(str(y) for y in sorted(train_years))
    return os.path.join(CACHE_DIR, f"history_{key}.pkl")


def load_history(train_years=(2024, 2025), force_refresh=False) -> pd.DataFrame:
    """Load race results for all completed races in the given years."""
    _ensure_cache_dir()
    cache_path = _history_cache_path(train_years)

    if not force_refresh and os.path.exists(cache_path):
        print("Loading historical data from cache...")
        return pd.read_pickle(cache_path)

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

                rows.append({
                    "year": year,
                    "round": round_num,
                    "event_name": event_name,
                    "driver": driver.get("Abbreviation", ""),
                    "team": driver.get("TeamName", ""),
                    "grid_position": int(grid) if not pd.isna(grid) else 20,
                    "finish_position": position,
                })
            print(f"  Loaded {year} R{round_num}: {event_name}")

    df = pd.DataFrame(rows)
    df.to_pickle(cache_path)
    print(f"Saved {len(df)} driver-race rows to cache.")
    return df


def load_qualifying(year: int, race) -> pd.DataFrame:
    """Load qualifying session — best of Q3/Q2/Q1 per driver."""
    _ensure_cache_dir()
    print(f"Fetching qualifying data: {year} {race}...")

    try:
        session = fastf1.get_session(year, race, "Q")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
    except Exception as e:
        raise RuntimeError(f"Could not load qualifying session for {year} {race}: {e}")

    results = session.results
    if results is None or results.empty:
        raise RuntimeError(f"No qualifying results found for {year} {race}")

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

        grid = driver.get("GridPosition")
        if pd.isna(grid):
            grid = driver.get("Position", 20)

        rows.append({
            "driver": driver.get("Abbreviation", ""),
            "team": driver.get("TeamName", ""),
            "qualifying_time_s": q_time,
            "grid_position": int(grid) if not pd.isna(grid) else 20,
        })

    return pd.DataFrame(rows)


def load_practice_pace(year: int, race) -> pd.DataFrame:
    """Load race pace proxy data.

    Normal weekends  → FP2 long runs (TyreLife > 3, race compounds).
    Sprint weekends  → Sprint race laps (skip lap 1 for standing-start noise).

    Returns a DataFrame with columns: driver, practice_pace_s (median lap time in seconds).
    """
    _ensure_cache_dir()

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
            laps = laps[laps["IsAccurate"] & (laps["LapNumber"] > 1)]
        else:
            print(f"  Loading FP2 long runs for {year} {race}...")
            session = fastf1.get_session(year, race, "FP2")
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            laps = session.laps.copy()
            laps = laps[
                laps["IsAccurate"]
                & (laps["TyreLife"] > 3)
                & (laps["Compound"].isin(["SOFT", "MEDIUM", "HARD"]))
            ]
    except Exception as e:
        print(f"  Warning: Could not load practice/sprint data for {year} {race}: {e}")
        return pd.DataFrame(columns=["driver", "practice_pace_s"])

    if laps.empty:
        print(f"  Warning: No usable practice laps found for {year} {race}")
        return pd.DataFrame(columns=["driver", "practice_pace_s"])

    laps["lap_time_s"] = laps["LapTime"].dt.total_seconds()
    laps = laps[laps["lap_time_s"].notna() & (laps["lap_time_s"] > 60)]

    pace = (
        laps.groupby("Driver")["lap_time_s"]
        .median()
        .reset_index()
        .rename(columns={"Driver": "driver", "lap_time_s": "practice_pace_s"})
    )

    print(f"  Practice pace loaded for {len(pace)} drivers.")
    return pace


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
