"""Tests for the /races route and the race-key resolution logic.

The route is tested with the service monkeypatched so no FastF1 network call
runs. ff1_to_race_key is pure and tested directly — it encodes the Madrid vs
Barcelona (two Spanish GPs) fix that this app depends on.
"""
from backend.app.services.race_service import ff1_to_race_key


def test_round_map_resolves_two_spanish_races():
    # R7 Barcelona GP and R14 Spanish GP both have country "Spain" — the
    # round-number map must disambiguate them.
    assert ff1_to_race_key("Spain", "Barcelona Grand Prix", year=2026, round_num=7) == "Spain"
    assert ff1_to_race_key("Spain", "Spanish Grand Prix", year=2026, round_num=14) == "Madrid"


def test_round_map_takes_priority_over_country():
    # Round 4 is Miami even though FastF1 country is "United States".
    assert ff1_to_race_key("United States", "Miami Grand Prix", year=2026, round_num=4) == "Miami"


def test_country_fallback_when_no_round():
    assert ff1_to_race_key("Monaco", "Monaco Grand Prix") == "Monaco"
    assert ff1_to_race_key("United Kingdom", "British Grand Prix") == "Britain"


def test_keyword_fallback_for_spanish_gp_without_round():
    # Without a round number, the "spanish grand prix" keyword routes to Madrid.
    assert ff1_to_race_key("Spain", "Spanish Grand Prix") == "Madrid"


def test_unknown_country_returns_none():
    assert ff1_to_race_key("Atlantis", "Atlantis Grand Prix") is None


def test_races_route_shapes_and_validates(client, monkeypatch):
    fixture = [
        {"name": "Australia", "round": 1, "date": "2026-03-08", "status": "completed"},
        {"name": "Madrid",    "round": 14, "date": "2026-09-13", "status": "current"},
    ]
    monkeypatch.setattr("backend.app.routes.races.list_races", lambda year: fixture)
    resp = client.get("/races?year=2026")
    assert resp.status_code == 200
    body = resp.json()
    assert body == fixture
    assert {"name", "round", "date", "status"} == set(body[0].keys())


def test_races_route_500_on_service_error(client, monkeypatch):
    def boom(year):
        raise RuntimeError("Could not load schedule: offline")
    monkeypatch.setattr("backend.app.routes.races.list_races", boom)
    resp = client.get("/races?year=2026")
    assert resp.status_code == 500
    assert "Could not load schedule" in resp.json()["detail"]
