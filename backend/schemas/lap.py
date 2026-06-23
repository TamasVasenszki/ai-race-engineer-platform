import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LapCreate(BaseModel):
    session_id: uuid.UUID
    lap_number: int
    lap_time_ms: int
    sector1_ms: int | None = None
    sector2_ms: int | None = None
    sector3_ms: int | None = None
    max_speed_kmh: float | None = None


class LapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    lap_number: int
    lap_time_ms: int
    sector1_ms: int | None
    sector2_ms: int | None
    sector3_ms: int | None
    max_speed_kmh: float | None
    ai_summary: str | None
    ai_recommendations: list[str] | None
    created_at: datetime
