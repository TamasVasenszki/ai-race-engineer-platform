import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Lap, RacingSession
from schemas.lap import LapResponse
from schemas.session import SessionCreate, SessionResponse

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> RacingSession:
    session = RacingSession(**body.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[RacingSession]:
    result = await db.execute(select(RacingSession).order_by(RacingSession.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RacingSession:
    session = await db.get(RacingSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/laps", response_model=list[LapResponse])
async def list_session_laps(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[Lap]:
    session = await db.get(RacingSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    result = await db.execute(
        select(Lap).where(Lap.session_id == session_id).order_by(Lap.lap_number)
    )
    return list(result.scalars().all())
