import asyncio

from fastapi import APIRouter, HTTPException

from backend.app.schemas.prediction import PredictionResponse, PredictRequest
from backend.app.services.prediction_service import generate_prediction

router = APIRouter()

# Serialise concurrent predict calls — FastF1 and pickle cache access is not
# thread-safe and simultaneous requests cause a segfault on Render.
_predict_lock = asyncio.Lock()


@router.post("/predict", response_model=PredictionResponse)
async def predict(req: PredictRequest):
    async with _predict_lock:
        try:
            return generate_prediction(req.race, req.year, req.force_refresh)
        except RuntimeError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
