from __future__ import annotations

import json
import logging

import httpx

from .base import AIProvider, AnalysisResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert Formula 1 race engineer. "
    "Analyze the lap telemetry provided and respond with a JSON object containing exactly:\n"
    '- "summary": a 1-2 sentence plain-English performance summary\n'
    '- "recommendations": an array of 2-3 concise, actionable engineer recommendations\n\n'
    "Example response:\n"
    '{"summary": "Solid lap at 1:35.5 with good top speed, but sector 2 is 0.8s off '
    'the pace due to a late apex at turn 6.", "recommendations": ["Brake 5m later into '
    'turn 3 to carry more speed", "Use more kerb on the exit of turn 6"]}'
)


def _build_user_prompt(lap_data: dict) -> str:
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


def _parse_analysis(raw: str) -> AnalysisResult | None:
    """Parse JSON response into AnalysisResult, return None on failure."""
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


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120.0)

    async def _chat(self, lap_data: dict) -> httpx.Response:
        return await self._client.post(
            "/api/chat",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(lap_data)},
                ],
                "format": "json",
                "stream": False,
            },
        )

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        try:
            response = await self._chat(lap_data)
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

        raw = response.json()["message"]["content"]
        result = _parse_analysis(raw)
        if result is not None:
            return result

        logger.warning("OllamaProvider: invalid JSON on first attempt, retrying")
        try:
            retry_response = await self._chat(lap_data)
            retry_response.raise_for_status()
            raw = retry_response.json()["message"]["content"]
        except (httpx.HTTPError, KeyError):
            raw = raw  # keep original raw for fallback

        result = _parse_analysis(raw)
        if result is not None:
            return result

        logger.warning("OllamaProvider: JSON retry failed, returning raw response as summary")
        return AnalysisResult(
            summary=raw,
            recommendations=["JSON parsing failed — raw response returned as summary"],
            provider="ollama",
        )
