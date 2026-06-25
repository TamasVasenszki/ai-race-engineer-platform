import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .session import RacingSession


class Lap(Base):
    __tablename__ = "laps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("racing_sessions.id"), nullable=False)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    sector1_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sector2_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sector3_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    racing_session: Mapped["RacingSession"] = relationship(
        "RacingSession", back_populates="laps"
    )
