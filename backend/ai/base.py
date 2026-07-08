from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    summary: str
    recommendations: list[str]
    provider: str


@dataclass
class Incident:
    lap_number: int
    severity: str
    description: str
    root_cause: str
    recommendations: list[str] = field(default_factory=list)


@dataclass
class IncidentReport:
    incidents: list[Incident]
    provider: str


class AIProvider(ABC):
    @abstractmethod
    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        """Analyze a single lap's telemetry and return engineer feedback."""
        ...

    async def analyze_incidents(
        self, laps: list[dict], session_info: dict
    ) -> IncidentReport:
        raise NotImplementedError(
            f"{type(self).__name__} does not support incident analysis"
        )
