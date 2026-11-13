import logging
import os
from datetime import datetime, timezone
import fastf1
import numpy as np
import pandas as pd
import unicodedata
from ml.config import CACHE_DIR
from ml.grid_refresh import refresh_cached_grid
from ml.config import CACHE_DIR
from ml.openf1_pace import load_openf1_pace_laps

# Suppress FastF1's verbose INFO chatter — we print our own progress messages.
# WARNING and above (accuracy checks, tyre corrections, etc.) stay visible.
logging.getLogger("fastf1").setLevel(logging.WARNING)

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


def _count_completed_rounds(years) -> int:
    """Count total completed rounds across the given years for cache-key freshness."""
    now = datetime.now(timezone.utc)
    total = 0
    for year in sorted(years):
        try:
            sched = fastf1.get_event_schedule(year, include_testing=False)
            total += int(
                (pd.to_datetime(sched["EventDate"], utc=True) < now).sum()
            )
        except Exception:
            pass
    return total


def _history_cache_path(train_years) -> str:
    key = "_".join(str(y) for y in sorted(train_years))
    n = _count_completed_rounds(train_years)
    return os.path.join(CACHE_DIR, f"history_{key}_r{n}_v3.pkl")


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
                grid = pd.to_numeric(grid, errors="coerce")

                valid_grid = (
                    pd.notna(grid)
                    and grid > 0
                    and float(grid).is_integer()
                )

                grid_position = int(grid) if valid_grid else float("nan")

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
                    "grid_position": grid_position,
                    "finish_position": position,
                    "finished": finished,
                })
            print(f"  Loaded {year} R{round_num}: {event_name}")

    df = pd.DataFrame(rows)
    df.to_pickle(cache_path)
    print(f"Saved {len(df)} driver-race rows to cache.")
    return df


def normalize_name(name):
    name = unicodedata.normalize("NFKD", str(name))
    return "".join(
        c for c in name if not unicodedata.combining(c)
    ).casefold().strip()

# Reverse of _LOCATION_CANONICAL: canonical race name → OpenF1 location string.
_RACE_TO_OPENF1_LOCATION: dict[str, str] = {v: k for k, v in _LOCATION_CANONICAL.items()}



def fetch_starting_grid_openf1(year: int, race: str, driver_num_to_abbr: dict[str, str]) -> dict[str, int]:
    """Return {driver_abbr: grid_position} from OpenF1 /v1/starting_grid.

    This reflects the FIA-published starting grid AFTER penalties are applied,
    and is available as soon as qualifying results are official — making it the
    correct pre-race grid source when the race session hasn't run yet.
    Falls back to {} on any network or parse failure.
    """
    try:
        import requests

        # Resolve OpenF1 location from canonical race name (e.g. "Italy" → "Monza").
        location_hint = _RACE_TO_OPENF1_LOCATION.get(race, race)
        race_lower = normalize_name(race)
        location_lower = normalize_name(location_hint)

        meetings = requests.get(
            "https://api.openf1.org/v1/meetings",
            params={"year": year},
            timeout=10,
        ).json()

        if not isinstance(meetings, list):
            return {}

        meeting_key = None
        for m in meetings:
            if not isinstance(m, dict):
                continue
            m_loc = normalize_name(m.get("location", ""))
            m_country = normalize_name(m.get("country_name", ""))
            m_name = normalize_name(m.get("meeting_name", ""))
            if location_lower in m_loc or race_lower in m_country or race_lower in m_name:
                meeting_key = m["meeting_key"]
                break

        if meeting_key is None:
            return {}

        sessions = requests.get(
            "https://api.openf1.org/v1/sessions",
            params={"meeting_key": meeting_key},
            timeout=10,
        ).json()

        if not isinstance(sessions, list):
            return {}

        qualifying_sessions = [
            s for s in sessions
            if isinstance(s, dict)
            and s.get("session_name") == "Qualifying"
        ]

        if not qualifying_sessions:
            return {}

        session_key = qualifying_sessions[0]["session_key"]

        grid_data = requests.get(
            "https://api.openf1.org/v1/starting_grid",
            params={"session_key": session_key},
            timeout=10,
        ).json()
        if not isinstance(grid_data, list) or not grid_data:
            return {}

        result = {}
        for row in grid_data:
            if not isinstance(row, dict):
                continue
            abbr = driver_num_to_abbr.get(str(row.get("driver_number", "")))
            if abbr and row.get("position") is not None:
                result[abbr] = int(row["position"])

        return result

    except Exception as e:
        print(f"  OpenF1 starting grid fetch failed: {e}")
        return {}


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
        # FastF1 reports GridPosition as -1 (or 0) when the source has no grid
        # data yet — common for very recent races that have results but no
        # published grid. Treat those as missing so callers keep the real
        # qualifying grid instead of a corrupted all-equal one.
        return {
            r.get("Abbreviation", ""): int(r.get("GridPosition"))
            for _, r in res.iterrows()
            if r.get("Abbreviation", "")
            and not pd.isna(r.get("GridPosition"))
            and int(r.get("GridPosition")) > 0
        }
    except Exception:
        return {}


def load_qualifying(year: int, race, force_refresh: bool = False) -> pd.DataFrame:
    """Load GP qualifying and determine the GP starting grid.

    Priority:
      1. Complete, valid OpenF1 official GP grid, including applicable penalties.
      2. GP qualifying classification as a provisional fallback.

    Never use Sprint qualifying or Sprint race positions as the GP grid.
    Never use a race-session fallback without validating its provenance.
    """
    _ensure_cache_dir()
    cache_path = _session_cache_path("quali", year, race)

    cached = (
        pd.read_pickle(cache_path)
        if os.path.exists(cache_path)
        else None
    )

    if not force_refresh and cached is not None:
        updated = refresh_cached_grid(
            year, race, cached, fetch_starting_grid_openf1
        )

        if updated is not cached:
            updated.to_pickle(cache_path)

        return updated

    print(f"Fetching qualifying data: {year} {race}...")

    try:
        session = fastf1.get_session(year, race, "Q")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
    except Exception as e:
        raise RuntimeError(f"Could not load qualifying session for {year} {race}: {e}")

    results = session.results
    if results is None or results.empty:
        raise RuntimeError(f"No qualifying results found for {year} {race}")

    # Build driver_number → abbreviation map for OpenF1 lookup.
    driver_num_to_abbr = {
        str(int(r.get("DriverNumber", 0))): r.get("Abbreviation", "")
        for _, r in results.iterrows()
        if r.get("Abbreviation", "")
    }

    # Try OpenF1 starting_grid first (penalty-corrected, available pre-race).
    # Fall back to race session GridPosition (post-race only).
    actual_grid = (
        fetch_starting_grid_openf1(
            year, str(race), driver_num_to_abbr
        )
        if force_refresh else {}
    )

    expected_drivers = {
        str(r.get("Abbreviation", ""))
        for _, r in results.iterrows()
        if r.get("Abbreviation", "")
    }

    valid_official_grid = {}
    for driver, position in actual_grid.items():
        if driver not in expected_drivers:
            continue
        try:
            position = int(position)
        except (TypeError, ValueError):
            continue
        if position > 0:
            valid_official_grid[driver] = position

    positions = list(valid_official_grid.values())
    official_grid_is_valid = (
        bool(expected_drivers)
        and set(valid_official_grid) == expected_drivers
        and len(positions) == len(set(positions))
    )

    # Preserve previously cached OpenF1 grid if the API fails.
    retained_cached_grid = False

    if not official_grid_is_valid and cached is not None:
        required = {"driver", "grid_position", "grid_source"}

        if required.issubset(cached.columns):
            old_grid = pd.to_numeric(
                cached["grid_position"], errors="coerce"
            )

            if (
                len(cached) == len(expected_drivers)
                and cached["driver"].is_unique
                and set(cached["driver"]) == expected_drivers
                and cached["grid_source"].eq("openf1").all()
                and old_grid.notna().all()
                and old_grid.gt(0).all()
                and old_grid.is_unique
                and (old_grid % 1 == 0).all()
            ):
                valid_official_grid = dict(zip(
                    cached["driver"], old_grid.astype(int)
                ))
                official_grid_is_valid = True
                retained_cached_grid = True

    if official_grid_is_valid:
        actual_grid = valid_official_grid

        if retained_cached_grid:
            print("  GP grid source: retained cached OpenF1 grid.")
        else:
            print("  GP grid source: complete OpenF1 official grid.")
    else:
        actual_grid = {}
        print("  GP grid source: provisional GP qualifying order.")

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


        if official_grid_is_valid:
            grid = actual_grid[drv_abbr]
        else:
            qualifying_position = driver.get("Position")
            try:
                grid = int(qualifying_position)
                if grid < 1:
                    raise ValueError("Invalid qualifying position")
            except (TypeError, ValueError):
                # Defensive fallback for missing qualifying classification.
                grid = len(rows) + 1

        rows.append({
            "driver": drv_abbr,
            "driver_number": str(int(driver.get("DriverNumber", 0))),
            "team": driver.get("TeamName", ""),
            "qualifying_time_s": q_time,
            "grid_position": grid,
            "grid_source": (
                "openf1" if official_grid_is_valid
                else "fastf1_qualifying"
            ),
        })

    df = pd.DataFrame(rows)

    if not force_refresh:
        df = refresh_cached_grid(
            year, race, df, fetch_starting_grid_openf1
        )

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

    
    def filter_laps(raw):
        if raw is None or raw.empty:
            return pd.DataFrame()

        mask = (
            raw["IsAccurate"].fillna(False).astype(bool)
            & raw["Compound"].isin(["SOFT", "MEDIUM", "HARD"])
        )

        if is_sprint:
            mask &= raw["LapNumber"] > 1
        else:
            mask &= raw["TyreLife"] >= 3

        return raw.loc[mask].copy()

    session = None
    laps = pd.DataFrame()
    pace_source = "fastf1"

    try:
        code = "S" if is_sprint else "FP2"
        session = fastf1.get_session(year, race, code)

        session.load(
            laps=True,
            telemetry=False,
            weather=False,
            messages=False,
        )

        laps = filter_laps(session.laps.copy())

    except Exception as e:
        print(f"  FastF1 pace unavailable: {e}")

    # Try OpenF1 if FastF1 fails or has no usable laps.
    if laps.empty:
        try:
            print(f"  Trying OpenF1 pace fallback: {year} {race}")

            laps = filter_laps(
                load_openf1_pace_laps(
                    year, race, is_sprint=is_sprint
                )
            )

            pace_source = "openf1"

        except Exception as e:
            print(f"  OpenF1 pace fallback failed: {e}")

    if laps.empty:
        print("  Warning: No usable practice/sprint laps.")
        return pd.DataFrame(
            columns=["driver", "practice_pace_s", "degradation_rate"]
        )

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
    
    stint_slopes = {}

    for (driver, stint), slaps in laps.groupby(["Driver", "Stint"]):
        slaps = slaps.dropna(
            subset=["TyreLife", "lap_time_s", "fuel_corrected_s"]
        )

        if len(slaps) < 5:
            continue

        # Remove unusually slow or fast laps within each stint.
        median_time = slaps["lap_time_s"].median()

        clean = slaps[
            slaps["lap_time_s"].between(
                median_time - 3.0,
                median_time + 3.0
            )
        ]

        if len(clean) < 5 or clean["TyreLife"].nunique() < 3:
            continue

        x = clean["TyreLife"].to_numpy(dtype=float)
        y = clean["fuel_corrected_s"].to_numpy(dtype=float)

        if not (np.isfinite(x).all() and np.isfinite(y).all()):
            continue

        slope = float(np.polyfit(x, y, 1)[0])

        if np.isfinite(slope):
            stint_slopes.setdefault(driver, []).append(slope)

    deg_rows = []

    for driver in laps["Driver"].dropna().unique():
        slopes = stint_slopes.get(driver, [])

        deg_rows.append({
            "driver": driver,
            "degradation_rate": (
                float(np.median(slopes))
                if slopes else float("nan")
            ),
        })


    deg_df = pd.DataFrame(deg_rows)
    result = pace_median.merge(deg_df, on="driver", how="left")

    # ── Teammate fallback for drivers with no valid laps ──────────────────────
    # When FastF1 marks all of a driver's laps as inaccurate they get no pace
    # entry. Rather than filling with worst-pace (penalises them unfairly), use
    # the teammate's pace as a proxy — same car, same weekend conditions.
    try:
        team_results = session.results if session is not None else None
    except Exception:
        team_results = None

    if team_results is not None and not team_results.empty:
        team_map = {
            r.get("Abbreviation", ""): r.get("TeamName", "")
            for _, r in team_results.iterrows()
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
    result.attrs["practice_source"] = pace_source
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
        # FastF1 creates a stub race session before the race runs with all
        # Position values as NaN. Require at least one real position to confirm
        # the race has actually finished.
        if res["Position"].isna().all():
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
