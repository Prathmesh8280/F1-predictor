
import fastf1
import pandas as pd
import requests


def load_openf1_pace_laps(year, race, is_sprint=False):
    """Convert OpenF1 laps/stints into FastF1-compatible lap data."""

    session_code = "S" if is_sprint else "FP2"
    session_name = "Sprint" if is_sprint else "Practice 2"

    target = pd.Timestamp(
        fastf1.get_session(year, race, session_code).date
    )

    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    else:
        target = target.tz_convert("UTC")

    base = "https://api.openf1.org/v1"

    def fetch(endpoint, params):
        response = requests.get(
            f"{base}/{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError(f"Invalid OpenF1 {endpoint} response")
        return pd.DataFrame(data)

    # Match by session name and scheduled time, not race-name strings.
    sessions = fetch(
        "sessions",
        {"year": year, "session_name": session_name},
    )

    if sessions.empty:
        raise ValueError(f"No OpenF1 {session_name} session")

    sessions["start"] = pd.to_datetime(
        sessions["date_start"], utc=True, format="ISO8601"
    )
    differences = (sessions["start"] - target).abs()
    match = sessions.loc[differences.idxmin()]

    if differences.min() > pd.Timedelta(hours=12):
        raise ValueError("No matching OpenF1 session")

    key = int(match["session_key"])

    laps = fetch("laps", {"session_key": key})
    stints = fetch("stints", {"session_key": key})
    drivers = fetch("drivers", {"session_key": key})

    if laps.empty or stints.empty or drivers.empty:
        raise ValueError("Incomplete OpenF1 pace data")

    # Driver number -> three-letter abbreviation.
    driver_map = {
        str(row["driver_number"]): row["name_acronym"]
        for _, row in drivers.iterrows()
    }

    laps["driver_number"] = pd.to_numeric(
        laps["driver_number"], errors="coerce"
    )
    laps["LapNumber"] = pd.to_numeric(
        laps["lap_number"], errors="coerce"
    )
    laps["Driver"] = (
        laps["driver_number"]
        .astype("Int64").astype(str)
        .map(driver_map)
    )

    # Convert lap durations and timestamps.
    duration = pd.to_numeric(
        laps["lap_duration"], errors="coerce"
    )
    laps["LapTime"] = pd.to_timedelta(duration, unit="s")
    laps["Time"] = (
        pd.to_datetime(
            laps["date_start"], utc=True, format="ISO8601"
        )
        - target
    )

    # Reconstruct compound and tyre life from stint ranges.
    laps["Compound"] = None
    laps["TyreLife"] = float("nan")
    laps["Stint"] = pd.Series(pd.NA, index=laps.index, dtype="Int64")

    for _, stint in stints.iterrows():
        if pd.isna(stint.get("lap_start")):
            continue

        start = int(stint["lap_start"])
        end = stint.get("lap_end")
        end = int(end) if pd.notna(end) else float("inf")

        mask = (
            (laps["driver_number"] == int(stint["driver_number"]))
            & laps["LapNumber"].between(start, end)
        )

        age = stint.get("tyre_age_at_start")
        age = float(age) if pd.notna(age) else 0.0

        laps.loc[mask, "Compound"] = stint["compound"]
        laps.loc[mask, "Stint"] = int(stint["stint_number"])
        laps.loc[mask, "TyreLife"] = (
            age + laps.loc[mask, "LapNumber"] - start + 1
        )

    # OpenF1 doesn't provide FastF1's IsAccurate flag.
    # Exclude obvious pit-out and pit-entry laps.
    pit_out = laps["is_pit_out_lap"].fillna(False).astype(bool)

    pit_in = pd.Series(False, index=laps.index)
    if "segments_sector_3" in laps.columns:
        pit_in = laps["segments_sector_3"].apply(
            lambda x: isinstance(x, list) and 2064 in x
        )

    laps["IsAccurate"] = (
        duration.gt(60)
        & ~pit_out
        & ~pit_in
        & laps["Driver"].notna()
        & laps["TyreLife"].notna()
    )

    return laps[[
        "Driver", "LapTime", "LapNumber",
        "IsAccurate", "TyreLife", "Compound", "Time", "Stint",
    ]]
