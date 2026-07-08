from pydantic import BaseModel


class IncidentResponse(BaseModel):
    lap_number: int
    severity: str
    description: str
    root_cause: str
    recommendations: list[str]


class IncidentReportResponse(BaseModel):
    incidents: list[IncidentResponse]
    provider: str
