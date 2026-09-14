"""Tests for the /predict route and prediction_service shaping + caching.

The ML pipeline (ml.predictor.run) and actual-results loader are monkeypatched
with fakes so no model training or FastF1 network call runs.
"""
import pandas as pd
import pytest

from backend.app.services import prediction_service as svc


@pytest.fixture(autouse=True)
def _clear_cache():
    svc._pred_cache.clear()
    yield
    svc._pred_cache.clear()


def _fake_results():
    return pd.DataFrame([
        {"predicted_rank": 1, "driver": "LEC", "team": "Ferrari", "grid_position": 3,
         "championship_rank": 4, "constructor_rank": 3, "fp2_pace_rank": 1,
         "delta1": 1.4, "stage2_used": True},
        {"predicted_rank": 2, "driver": "RUS", "team": "Mercedes", "grid_position": 2,
         "championship_rank": 2, "constructor_rank": 2, "fp2_pace_rank": 3,
         "delta1": 0.0, "stage2_used": True},
    ])


def _fake_backtest():
    return {"model_mae_fin": 2.08, "baseline_mae_fin": 2.19}


def test_generate_prediction_shape(monkeypatch):
    monkeypatch.setattr(svc, "run", lambda **kw: (_fake_results(), _fake_backtest()))
    monkeypatch.setattr(svc.dl, "load_actual_results", lambda year, race: None)

    out = svc.generate_prediction("Italy", 2026, force_refresh=False)

    assert set(out.keys()) == {"race", "year", "circuit", "predictions", "is_completed", "model_mae", "baseline_mae"}
    assert out["race"] == "Italy" and out["year"] == 2026
    assert out["is_completed"] is False
    assert out["circuit"]["name"] == "Autodromo Nazionale Monza"
    assert out["model_mae"] == 2.08 and out["baseline_mae"] == 2.19
    # Sorted by rank; actual_rank None when race not completed.
    assert [p["rank"] for p in out["predictions"]] == [1, 2]
    assert out["predictions"][0]["driver"] == "LEC"
    assert out["predictions"][0]["actual_rank"] is None


def test_generate_prediction_merges_actual_results(monkeypatch):
    monkeypatch.setattr(svc, "run", lambda **kw: (_fake_results(), _fake_backtest()))
    actual = pd.DataFrame([{"driver": "LEC", "actual_position": 22}, {"driver": "RUS", "actual_position": 2}])
    monkeypatch.setattr(svc.dl, "load_actual_results", lambda year, race: actual)

    out = svc.generate_prediction("Italy", 2026)
    assert out["is_completed"] is True
    by_driver = {p["driver"]: p for p in out["predictions"]}
    assert by_driver["LEC"]["actual_rank"] == 22
    assert by_driver["RUS"]["actual_rank"] == 2


def test_cache_prevents_second_pipeline_run(monkeypatch):
    calls = {"n": 0}

    def counting_run(**kw):
        calls["n"] += 1
        return _fake_results(), _fake_backtest()

    fake_actuals = pd.DataFrame([
        {"driver": "LEC", "actual_position": 1},
        {"driver": "RUS", "actual_position": 2},
    ])

    monkeypatch.setattr(svc, "run", counting_run)
    # Completed race → result gets cached → second call is a cache hit
    monkeypatch.setattr(svc.dl, "load_actual_results", lambda year, race: fake_actuals)

    svc.generate_prediction("Italy", 2026)
    svc.generate_prediction("Italy", 2026)  # served from cache
    assert calls["n"] == 1

    svc.generate_prediction("Italy", 2026, force_refresh=True)  # bypasses cache
    assert calls["n"] == 2


def test_incomplete_race_not_cached(monkeypatch):
    calls = {"n": 0}

    def counting_run(**kw):
        calls["n"] += 1
        return _fake_results(), _fake_backtest()

    monkeypatch.setattr(svc, "run", counting_run)
    # Race not finished → never cached → every request re-runs pipeline
    monkeypatch.setattr(svc.dl, "load_actual_results", lambda year, race: None)

    svc.generate_prediction("Italy", 2026)
    svc.generate_prediction("Italy", 2026)
    assert calls["n"] == 2


def test_unknown_circuit_uses_safe_defaults(monkeypatch):
    monkeypatch.setattr(svc, "run", lambda **kw: (_fake_results(), _fake_backtest()))
    monkeypatch.setattr(svc.dl, "load_actual_results", lambda year, race: None)
    out = svc.generate_prediction("Atlantis", 2026)
    assert out["circuit"]["country_code"] == "un"
    assert out["circuit"]["name"] == "Atlantis"


def test_predict_route_200(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routes.predictions.generate_prediction",
        lambda race, year, force_refresh: {
            "race": race, "year": year,
            "circuit": {"name": "X", "country_code": "un", "overtaking": "MEDIUM", "track_img_url": ""},
            "predictions": [{"rank": 1, "driver": "LEC", "team": "Ferrari", "grid_pos": 3}],
            "is_completed": False, "model_mae": None, "baseline_mae": None,
        },
    )
    resp = client.post("/predict", json={"race": "Italy", "year": 2026, "force_refresh": False})
    assert resp.status_code == 200
    assert resp.json()["predictions"][0]["driver"] == "LEC"


def test_predict_route_404_on_runtime_error(client, monkeypatch):
    def boom(race, year, force_refresh):
        raise RuntimeError("No qualifying data found")
    monkeypatch.setattr("backend.app.routes.predictions.generate_prediction", boom)
    resp = client.post("/predict", json={"race": "Madrid", "year": 2026})
    assert resp.status_code == 404
    assert "No qualifying data" in resp.json()["detail"]


def test_predict_route_500_on_unexpected_error(client, monkeypatch):
    def boom(race, year, force_refresh):
        raise ValueError("kaboom")
    monkeypatch.setattr("backend.app.routes.predictions.generate_prediction", boom)
    resp = client.post("/predict", json={"race": "Italy", "year": 2026})
    assert resp.status_code == 500
    assert "Prediction failed" in resp.json()["detail"]
