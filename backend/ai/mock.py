from .base import AIProvider, AnalysisResult


class MockProvider(AIProvider):
    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        lap_time = lap_data.get("lap_time_ms", 0)
        return AnalysisResult(
            summary=f"Mock analysis: lap completed in {lap_time}ms.",
            recommendations=[
                "Focus on braking consistency in sector 1.",
                "Trail brake deeper into turn 3.",
            ],
            provider="mock",
        )
