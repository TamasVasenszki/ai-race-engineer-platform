from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    summary: str
    recommendations: list[str]
    provider: str


class AIProvider(ABC):
    @abstractmethod
    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        """Analyze a single lap's telemetry and return engineer feedback."""
        ...
