from __future__ import annotations

import anthropic

from .base import AIProvider, AnalysisResult

_SYSTEM_PROMPT = (
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


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def analyze_lap(self, lap_data: dict) -> AnalysisResult:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_user_prompt(lap_data)}],
                tools=[_LAP_ANALYSIS_TOOL],
                tool_choice={"type": "tool", "name": "report_lap_analysis"},
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

        data = tool_block.input
        return AnalysisResult(
            summary=data["summary"],
            recommendations=data["recommendations"],
            provider="claude",
        )
