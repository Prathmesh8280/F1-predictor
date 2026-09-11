"""Prediction request and response schemas."""
from pydantic import BaseModel, ConfigDict


class PredictRequest(BaseModel):
    race: str
    year: int
    force_refresh: bool = False


class Circuit(BaseModel):
    name: str
    country_code: str
    overtaking: str
    track_img_url: str


class DriverPrediction(BaseModel):
    rank: int
    driver: str
    team: str
    grid_pos: int
    actual_rank: int | None = None
    championship_rank: int | None = None
    constructor_rank: int | None = None
    fp2_pace_rank: int | None = None
    delta1: float | None = None
    stage2_used: bool = False


class PredictionResponse(BaseModel):
    # model_mae/baseline_mae start with "model_"; clear the protected namespace
    # so Pydantic does not warn about it.
    model_config = ConfigDict(protected_namespaces=())

    race: str
    year: int
    circuit: Circuit
    predictions: list[DriverPrediction]
    is_completed: bool
    model_mae: float | None = None
    baseline_mae: float | None = None
