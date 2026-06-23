import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Lap
from schemas.lap import LapCreate, LapResponse

router = APIRouter()


@router.post("/", response_model=LapResponse, status_code=201)
async def create_lap(
    body: LapCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Lap:
    result = await request.app.state.ai_provider.analyze_lap(body.model_dump())
    lap = Lap(
        **body.model_dump(),
        ai_summary=result.summary,
        ai_recommendations=result.recommendations,
    )
    db.add(lap)
    await db.commit()
    await db.refresh(lap)
    return lap


@router.get("/{lap_id}", response_model=LapResponse)
async def get_lap(lap_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Lap:
    lap = await db.get(Lap, lap_id)
    if lap is None:
        raise HTTPException(status_code=404, detail="Lap not found")
    return lap
