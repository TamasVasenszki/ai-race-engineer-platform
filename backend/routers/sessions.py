import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import RacingSession
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
