from __future__ import annotations

import anthropic

from .base import AIProvider, AnalysisResult, Incident, IncidentReport

_LAP_SYSTEM_PROMPT = (
    "You are an expert Formula 1 race engineer. "
    "Analyze the lap telemetry provided and call report_lap_analysis "
    "with a concise performance summary and 2–3 actionable recommendations."
)

_LAP_ANALYSIS_TOOL = {
    "name": "report_lap_analysis",
    "description": "Report the structured analysis of a single race lap. Always call this tool.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1–2 sentence plain-English summary of lap performance.",
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2–3 concise, actionable engineer recommendations.",
                "minItems": 2,
                "maxItems": 3,
            },
        },
        "required": ["summary", "recommendations"],
    },
}

_INCIDENT_SYSTEM_PROMPT = (
    "You are an F1 race data analyst. Analyze the session lap data provided "
    "and call report_incident_analysis with any anomalies found — significant "
    "lap time increases, speed drops, or sector degradation patterns. "
    "If no anomalies are found, call the tool with an empty incidents array."
)

_INCIDENT_ANALYSIS_TOOL = {
    "name": "report_incident_analysis",
    "description": (
        "Report anomalies found in a racing session's lap data. "
        "Always call this tool, even if no incidents were found."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "incidents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "lap_number": {
                            "type": "integer",
                            "description": "The lap number where the incident occurred.",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["warning", "critical"],
                            "description": "warning for minor anomalies, critical for major.",
                        },
                        "description": {
                            "type": "string",
                            "description": "1-2 sentence description of the anomaly.",
                        },
                        "root_cause": {
                            "type": "string",
                            "description": "Probable cause of the incident.",
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "1-2 actionable suggestions.",
                        },
                    },
                    "required": [
                        "lap_number",
                        "severity",
                        "description",
                        "root_cause",
                        "recommendations",
                    ],
                },
            },
        },
        "required": ["incidents"],
    },
}


def _build_lap_prompt(lap_data: dict) -> str:
    parts = [f"Lap {lap_data['lap_number']}: total {lap_data['lap_time_ms']} ms"]
    if lap_data.get("sector1_ms") is not None:
        parts.append(f"S1={lap_data['sector1_ms']} ms")
    if lap_data.get("sector2_ms") is not None:
        parts.append(f"S2={lap_data['sector2_ms']} ms")
    if lap_data.get("sector3_ms") is not None:
        parts.append(f"S3={lap_data['sector3_ms']} ms")
    if lap_data.get("max_speed_kmh") is not None:
        parts.append(f"top speed {lap_data['max_speed_kmh']:.1f} km/h")
    return ", ".join(parts) + "."


def _build_incidents_prompt(laps: list[dict], session_info: dict) -> str:
    lines = [f"Session: {session_info.get('track', '?')}, {session_info.get('car', '?')}"]
    for lap in laps:
        line = f"Lap {lap['lap_number']}: {lap['lap_time_ms']} ms"
        if lap.get("max_speed_kmh") is not None:
            line += f", top speed {lap['max_speed_kmh']:.1f} km/h"
        if lap.get("sector1_ms") is not None:
            line += f", S1={lap['sector1_ms']} ms"
        if lap.get("sector2_ms") is not None:
            line += f", S2={lap['sector2_ms']} ms"
        if lap.get("sector3_ms") is not None:
            line += f", S3={lap['sector3_ms']} ms"
        lines.append(line)
    return "\n".join(lines)


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def _tool_call(
        self, system: str, user: str, tool: dict, tool_name: str
    ) -> dict:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )
        except anthropic.APIError as exc:
            raise RuntimeError(
                f"ClaudeProvider: Anthropic API error ({exc.status_code}): {exc.message}"
            ) from exc

        tool_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if tool_block is None:
            raise RuntimeError(
                f"ClaudeProvider: expected tool_use block not found. "
                f"stop_reason={response.stop_reason!r}"
            )
        return tool_block.input

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        data = await self._tool_call(
            _LAP_SYSTEM_PROMPT,
            _build_lap_prompt(lap_data),
            _LAP_ANALYSIS_TOOL,
            "report_lap_analysis",
        )
        return AnalysisResult(
            summary=data["summary"],
            recommendations=data["recommendations"],
            provider="claude",
        )

    async def analyze_incidents(
        self, laps: list[dict], session_info: dict
    ) -> IncidentReport:
        data = await self._tool_call(
            _INCIDENT_SYSTEM_PROMPT,
            _build_incidents_prompt(laps, session_info),
            _INCIDENT_ANALYSIS_TOOL,
            "report_incident_analysis",
        )
        incidents = [
            Incident(
                lap_number=item["lap_number"],
                severity=item["severity"],
                description=item["description"],
                root_cause=item["root_cause"],
                recommendations=item.get("recommendations", []),
            )
            for item in data.get("incidents", [])
        ]
        return IncidentReport(incidents=incidents, provider="claude")
