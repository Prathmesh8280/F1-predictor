"""Race schedule application logic — resolve FastF1 events to circuit keys and
build the ordered race list the frontend consumes.
"""
from datetime import date, timedelta

import fastf1

from backend.app.constants import CIRCUIT_META, EVENTNAME_KEYWORD, FF1_TO_KEY, ROUND_MAP


def ff1_to_race_key(country: str, event_name: str, year: int = 0, round_num: int = 0) -> str | None:
    """Resolve a FastF1 event to our canonical circuit key.

    Primary lookup is the year-scoped round-number map (unambiguous). Falls back
    to event-name keyword matching, then to country → key mapping.
    """
    # Primary: round-number map is unambiguous
    if year and round_num:
        key = ROUND_MAP.get(year, {}).get(round_num)
        if key:
            return key
    # Fallback: keyword matching then country mapping
    en = event_name.lower()
    for keyword, key in EVENTNAME_KEYWORD:
        if keyword in en:
            return key
    mapped = FF1_TO_KEY.get(country, country)
    return mapped if mapped in CIRCUIT_META else None


def list_races(year: int) -> list[dict]:
    """Return completed + current races for the season, sorted by round.

    Raises RuntimeError if the FastF1 schedule cannot be loaded.
    """
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as e:
        raise RuntimeError(f"Could not load schedule: {e}")

    today = date.today()
    cutoff = today + timedelta(days=4)  # include up to ~end of current race weekend

    races = []
    for _, ev in schedule.iterrows():
        event_date = ev["EventDate"]
        if hasattr(event_date, "date"):
            event_date = event_date.date()
        if event_date > cutoff:
            continue

        country = str(ev.get("Country", ""))
        event_name = str(ev.get("EventName", ""))
        round_num = int(ev["RoundNumber"])
        key = ff1_to_race_key(country, event_name, year=year, round_num=round_num)
        if key is None:
            continue

        status = "completed" if event_date < today else "current"
        races.append({
            "name": key,
            "round": round_num,
            "date": str(event_date),
            "status": status,
        })

    return sorted(races, key=lambda r: r["round"])
