from fastapi import APIRouter, HTTPException

from backend.app.schemas.race import RaceEntry
from backend.app.services.race_service import list_races

router = APIRouter()


@router.get("/races", response_model=list[RaceEntry])
def get_races(year: int = 2026):
    try:
        return list_races(year)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
