from .base import AIProvider, AnalysisResult, Incident, IncidentReport

_WARNING_THRESHOLD = 1.15
_CRITICAL_THRESHOLD = 1.50


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

    async def analyze_incidents(
        self, laps: list[dict], session_info: dict
    ) -> IncidentReport:
        if not laps:
            return IncidentReport(incidents=[], provider="mock")

        min_time = min(lap["lap_time_ms"] for lap in laps)
        incidents: list[Incident] = []

        for lap in laps:
            lap_time = lap["lap_time_ms"]
            ratio = lap_time / min_time

            if ratio >= _CRITICAL_THRESHOLD:
                incidents.append(Incident(
                    lap_number=lap["lap_number"],
                    severity="critical",
                    description=(
                        f"Lap {lap['lap_number']} was {ratio:.1f}x slower "
                        f"than the best lap ({lap_time} ms vs {min_time} ms)."
                    ),
                    root_cause="Possible off-track excursion or spin.",
                    recommendations=[
                        "Review corner entry speed.",
                        "Check for track limit violations.",
                    ],
                ))
            elif ratio >= _WARNING_THRESHOLD:
                incidents.append(Incident(
                    lap_number=lap["lap_number"],
                    severity="warning",
                    description=(
                        f"Lap {lap['lap_number']} was {ratio:.1f}x slower "
                        f"than the best lap ({lap_time} ms vs {min_time} ms)."
                    ),
                    root_cause="Inconsistent braking or suboptimal line through key corners.",
                    recommendations=[
                        "Focus on braking consistency.",
                        "Compare sector times to identify weak areas.",
                    ],
                ))

        return IncidentReport(incidents=incidents, provider="mock")
