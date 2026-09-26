"""Race listing response schema."""
from pydantic import BaseModel


class RaceEntry(BaseModel):
    name: str
    round: int
    date: str
    status: str  # "completed" | "current"
    winner: str | None = None  # winning driver abbreviation, completed races only
