from fastapi import APIRouter, HTTPException

from backend.app.schemas.prediction import PredictionResponse, PredictRequest
from backend.app.services.prediction_service import generate_prediction

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictRequest):
    try:
        return generate_prediction(req.race, req.year, req.force_refresh)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
