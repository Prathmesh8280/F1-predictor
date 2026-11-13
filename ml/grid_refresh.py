import requests
import fastf1
from datetime import datetime, timedelta, timezone
# Minutes after qualifying ends
GRID_CHECKPOINTS = (
    ("fastf1", 5),
    ("openf1_40m", 40),
    ("openf1_3h", 180),
    ("openf1_5h", 300),
)


def due_grid_checkpoint(quali_end, now, last_checkpoint=-1):
    """Return the latest due checkpoint, or None."""

    if quali_end.tzinfo is None or now.tzinfo is None:
        raise ValueError("Both timestamps must be timezone-aware")

    due = [
        i for i, (_, minutes) in enumerate(GRID_CHECKPOINTS)
        if now >= quali_end + timedelta(minutes=minutes)
    ]

    if not due:
        return None

    checkpoint = max(due)
    return checkpoint if checkpoint > last_checkpoint else None



def get_qualifying_end_utc(session_key: int):
    """Get the actual Q3 finish timestamp from OpenF1."""

    response = requests.get(
        "https://api.openf1.org/v1/race_control",
        params={
            "session_key": session_key,
            "category": "SessionStatus",
        },
        timeout=15,
    )
    response.raise_for_status()

    finishes = [
        datetime.fromisoformat(
            e["date"].replace("Z", "+00:00")
        )
        for e in response.json()
        if e.get("message") == "SESSION FINISHED"
        and str(e.get("qualifying_phase")) == "3"
    ]

    return max(finishes, default=None)


def get_qualifying_end_for_race(year: int, race):
    """Find the GP qualifying session and its actual Q3 end."""

    scheduled = fastf1.get_session(year, race, "Q").date

    # FastF1's Session.date is in UTC.
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    else:
        scheduled = scheduled.astimezone(timezone.utc)

    response = requests.get(
        "https://api.openf1.org/v1/sessions",
        params={
            "year": year,
            "session_name": "Qualifying",
        },
        timeout=15,
    )
    response.raise_for_status()

    matches = []

    for session in response.json():
        if session.get("session_name") != "Qualifying":
            continue

        start = datetime.fromisoformat(
            session["date_start"].replace("Z", "+00:00")
        )

        difference = abs(
            (start - scheduled).total_seconds()
        )

        if difference <= 6 * 3600:
            matches.append(
                (difference, session["session_key"])
            )

    if not matches:
        return None

    session_key = min(matches)[1]

    return get_qualifying_end_utc(session_key)


def _utc(value):
    """Convert a datetime to UTC."""
    if not isinstance(value, datetime):
        value = value.to_pydatetime()

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _now_utc():
    return datetime.now(timezone.utc)


def refresh_cached_grid(year, race, cached, fetch_grid, now=None):
    """Refresh starting grid at scheduled checkpoints."""

    now = _utc(now or _now_utc())

    updated = cached.copy()
    updated.attrs = dict(cached.attrs)

    # First successful FastF1 qualifying cache.
    # Do not contact OpenF1 on this request.
    first_seen = updated.attrs.get("grid_first_seen_utc")

    if not first_seen:
        updated.attrs["grid_first_seen_utc"] = now.isoformat()
        return updated

    try:
        first_seen_dt = _utc(datetime.fromisoformat(first_seen))
    except (TypeError, ValueError):
        updated.attrs["grid_first_seen_utc"] = now.isoformat()
        return updated

    try:
        q_start = _utc(fastf1.get_session(year, race, "Q").date)
        race_start = _utc(fastf1.get_session(year, race, "R").date)
    except Exception as exc:
        print(f"Grid refresh: schedule unavailable: {exc}")
        return updated

    if now >= race_start:
        return updated

    # Wait at least 35 minutes after FastF1 qualifying
    # was first cached, as well as 90 minutes from the
    # scheduled qualifying start.
    earliest_check = max(
        q_start + timedelta(minutes=90),
        first_seen_dt + timedelta(minutes=35),
    )

    if now < earliest_check:
        return updated


    # Reuse stored actual Q3 end time.
    end_str = updated.attrs.get("grid_quali_end_utc")

    if end_str:
        try:
            quali_end = datetime.fromisoformat(end_str)
        except ValueError:
            quali_end = None
    else:
        quali_end = None

    if quali_end is None:
        retry_after = updated.attrs.get(
            "grid_end_lookup_retry_after"
        )

        if retry_after and now < datetime.fromisoformat(retry_after):
            return cached

        try:
            quali_end = get_qualifying_end_for_race(year, race)
        except Exception as exc:
            print(f"Grid refresh: Q3 end unavailable: {exc}")
            quali_end = None

        if quali_end is None:
            updated.attrs["grid_end_lookup_retry_after"] = (
                now + timedelta(minutes=20)
            ).isoformat()
            return updated

        updated.attrs["grid_quali_end_utc"] = quali_end.isoformat()
        updated.attrs.pop("grid_end_lookup_retry_after", None)

    # Check the latest due checkpoint.
    last_checkpoint = int(
        updated.attrs.get("grid_last_checkpoint", 0)
    )

    due = due_grid_checkpoint(
        quali_end, now, last_checkpoint
    )

    if due is None or due == 0:
        return updated

    # Driver number -> abbreviation mapping.
    if "driver_number" in updated.columns:
        driver_map = dict(zip(
            updated["driver_number"].astype(str),
            updated["driver"]
        ))
    else:
        # Compatibility with older qualifying caches.
        driver_map = {}

        try:
            q = fastf1.get_session(year, race, "Q")
            q.load(
                laps=False,
                telemetry=False,
                weather=False,
                messages=False
            )

            driver_map = {
                str(int(r["DriverNumber"])): r["Abbreviation"]
                for _, r in q.results.iterrows()
                if r.get("Abbreviation")
            }
        except Exception as exc:
            print(f"Grid refresh: driver mapping failed: {exc}")

    # Record that this checkpoint was attempted.
    # A failure can be retried at the next checkpoint.
    updated.attrs["grid_last_checkpoint"] = due

    if not driver_map:
        return updated

    try:
        grid = fetch_grid(year, str(race), driver_map)
    except Exception as exc:
        print(f"Grid refresh: OpenF1 failed: {exc}")
        return updated

    # Validate complete grid before replacing anything.
    drivers = set(updated["driver"])

    try:
        normalized = {
            driver: int(pos)
            for driver, pos in grid.items()
            if driver in drivers
        }

        positions = list(normalized.values())

        valid = (
            bool(drivers)
            and len(updated) == len(drivers)
            and set(normalized) == drivers
            and all(p > 0 for p in positions)
            and len(positions) == len(set(positions))
        )
    except (TypeError, ValueError, AttributeError):
        valid = False

    checkpoint_name = GRID_CHECKPOINTS[due][0]

    if valid:
        updated["grid_position"] = (
            updated["driver"].map(normalized).astype(int)
        )
        updated["grid_source"] = "openf1"

        print(f"Grid refresh {checkpoint_name}: OpenF1 grid saved.")
    else:
        print(f"Grid refresh {checkpoint_name}: retaining cached grid.")

    return updated
