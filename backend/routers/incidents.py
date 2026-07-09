import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Lap, RacingSession
from schemas.incident import IncidentReportResponse

router = APIRouter()


@router.post("/{session_id}/incidents", response_model=IncidentReportResponse)
async def analyze_incidents(
    session_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    session = await db.get(RacingSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Lap)
        .where(Lap.session_id == session_id)
        .order_by(Lap.lap_number)
    )
    laps = list(result.scalars().all())

    if not laps:
        return {"incidents": [], "provider": request.app.state.ai_provider.__class__.__name__}

    lap_dicts = [
        {
            "lap_number": lap.lap_number,
            "lap_time_ms": lap.lap_time_ms,
            "sector1_ms": lap.sector1_ms,
            "sector2_ms": lap.sector2_ms,
            "sector3_ms": lap.sector3_ms,
            "max_speed_kmh": lap.max_speed_kmh,
        }
        for lap in laps
    ]
    session_info = {"track": session.track, "car": session.car}

    report = await request.app.state.ai_provider.analyze_incidents(
        lap_dicts, session_info
    )
    response = {
        "incidents": [
            {
                "lap_number": inc.lap_number,
                "severity": inc.severity,
                "description": inc.description,
                "root_cause": inc.root_cause,
                "recommendations": inc.recommendations,
            }
            for inc in report.incidents
        ],
        "provider": report.provider,
    }
    if report.incidents:
        await request.app.state.ws_manager.broadcast(
            {
                "type": "incident_alert",
                "session_id": str(session_id),
                "incidents": response["incidents"],
            }
        )
    return response
