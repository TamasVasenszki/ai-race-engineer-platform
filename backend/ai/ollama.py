from __future__ import annotations

import json
import logging

import httpx

from .base import AIProvider, AnalysisResult, Incident, IncidentReport

logger = logging.getLogger(__name__)

_LAP_SYSTEM_PROMPT = (
    "You are an expert Formula 1 race engineer. "
    "Analyze the lap telemetry provided and respond with a JSON object containing exactly:\n"
    '- "summary": a 1-2 sentence plain-English performance summary\n'
    '- "recommendations": an array of 2-3 concise, actionable engineer recommendations\n\n'
    "Example response:\n"
    '{"summary": "Solid lap at 1:35.5 with good top speed, but sector 2 is 0.8s off '
    'the pace due to a late apex at turn 6.", "recommendations": ["Brake 5m later into '
    'turn 3 to carry more speed", "Use more kerb on the exit of turn 6"]}'
)

_INCIDENT_SYSTEM_PROMPT = (
    "You are an F1 race data analyst. Analyze the session lap data below and identify "
    "anomalies — significant lap time increases, speed drops, or sector degradation.\n\n"
    "Respond with a JSON object containing exactly:\n"
    '- "incidents": an array of incident objects, each with:\n'
    '  - "lap_number": integer\n'
    '  - "severity": "warning" or "critical"\n'
    '  - "description": 1-2 sentence description of the anomaly\n'
    '  - "root_cause": probable cause of the incident\n'
    '  - "recommendations": array of 1-2 actionable suggestions\n\n'
    "If no anomalies are found, return {\"incidents\": []}.\n\n"
    "Example response:\n"
    '{"incidents": [{"lap_number": 3, "severity": "warning", '
    '"description": "Lap 3 was 12% slower than the session best.", '
    '"root_cause": "Late braking into turn 1 caused a lockup and wide exit.", '
    '"recommendations": ["Brake 10m earlier into turn 1", '
    '"Trail brake to maintain front grip"]}]}'
)


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


def _parse_analysis(raw: str) -> AnalysisResult | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data.get("summary"), str) or not isinstance(
        data.get("recommendations"), list
    ):
        return None
    return AnalysisResult(
        summary=data["summary"],
        recommendations=data["recommendations"],
        provider="ollama",
    )


def _parse_incident_report(raw: str) -> IncidentReport | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data.get("incidents"), list):
        return None
    incidents = []
    for item in data["incidents"]:
        if not isinstance(item, dict) or "lap_number" not in item:
            continue
        incidents.append(Incident(
            lap_number=item["lap_number"],
            severity=item.get("severity", "warning"),
            description=item.get("description", ""),
            root_cause=item.get("root_cause", ""),
            recommendations=item.get("recommendations", []),
        ))
    return IncidentReport(incidents=incidents, provider="ollama")


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120.0)

    async def _call(self, system: str, user: str) -> str:
        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "format": "json",
                    "stream": False,
                },
            )
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"OllamaProvider: cannot connect to Ollama at {self._base_url}. "
                "Is it running?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"OllamaProvider: request timed out after 120s "
                f"(model={self._model})"
            ) from exc

        if response.status_code == 404:
            raise RuntimeError(
                f"OllamaProvider: model '{self._model}' not found. "
                f"Run: ollama pull {self._model}"
            )
        response.raise_for_status()
        return response.json()["message"]["content"]

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        user_prompt = _build_lap_prompt(lap_data)
        raw = await self._call(_LAP_SYSTEM_PROMPT, user_prompt)

        result = _parse_analysis(raw)
        if result is not None:
            return result

        logger.warning("OllamaProvider: invalid JSON on first attempt, retrying")
        try:
            raw = await self._call(_LAP_SYSTEM_PROMPT, user_prompt)
        except (httpx.HTTPError, RuntimeError):
            pass

        result = _parse_analysis(raw)
        if result is not None:
            return result

        logger.warning("OllamaProvider: JSON retry failed, returning raw response")
        return AnalysisResult(
            summary=raw,
            recommendations=["JSON parsing failed — raw response returned as summary"],
            provider="ollama",
        )

    async def analyze_incidents(
        self, laps: list[dict], session_info: dict
    ) -> IncidentReport:
        user_prompt = _build_incidents_prompt(laps, session_info)
        raw = await self._call(_INCIDENT_SYSTEM_PROMPT, user_prompt)

        report = _parse_incident_report(raw)
        if report is not None:
            return report

        logger.warning("OllamaProvider: invalid incident JSON, retrying")
        try:
            raw = await self._call(_INCIDENT_SYSTEM_PROMPT, user_prompt)
        except (httpx.HTTPError, RuntimeError):
            pass

        report = _parse_incident_report(raw)
        if report is not None:
            return report

        logger.warning("OllamaProvider: incident JSON retry failed, returning fallback")
        return IncidentReport(
            incidents=[Incident(
                lap_number=0,
                severity="warning",
                description="Could not parse AI response.",
                root_cause=raw,
                recommendations=["Retry the analysis or check Ollama model output."],
            )],
            provider="ollama",
        )
