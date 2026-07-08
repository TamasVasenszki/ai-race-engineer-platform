import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    track: str
    car: str


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    track: str
    car: str
    created_at: datetime
