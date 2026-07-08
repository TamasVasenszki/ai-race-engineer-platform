from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ai.claude import ClaudeProvider
from ai.mock import MockProvider
from ai.ollama import OllamaProvider
from ai.openai import OpenAIProvider

_SESSION_INFO = {"track": "Monza", "car": "Ferrari 488 GT3"}


def _lap(number: int, time_ms: int, speed: float | None = None) -> dict:
    d: dict = {"lap_number": number, "lap_time_ms": time_ms}
    if speed is not None:
        d["max_speed_kmh"] = speed
    return d


# ---------------------------------------------------------------------------
# MockProvider tests
# ---------------------------------------------------------------------------

async def test_mock_no_anomalies() -> None:
    provider = MockProvider()
    laps = [_lap(1, 90000), _lap(2, 91000), _lap(3, 92000)]

    report = await provider.analyze_incidents(laps, _SESSION_INFO)

    assert report.provider == "mock"
    assert report.incidents == []


async def test_mock_warning_detected() -> None:
    provider = MockProvider()
    laps = [_lap(1, 90000), _lap(2, 108000)]  # 108000 / 90000 = 1.2x

    report = await provider.analyze_incidents(laps, _SESSION_INFO)

    assert len(report.incidents) == 1
    assert report.incidents[0].severity == "warning"
    assert report.incidents[0].lap_number == 2


async def test_mock_critical_detected() -> None:
    provider = MockProvider()
    laps = [_lap(1, 90000), _lap(2, 140000)]  # 140000 / 90000 = 1.56x

    report = await provider.analyze_incidents(laps, _SESSION_INFO)

    assert len(report.incidents) == 1
    assert report.incidents[0].severity == "critical"
    assert report.incidents[0].lap_number == 2


async def test_mock_mixed_severities() -> None:
    provider = MockProvider()
    laps = [_lap(1, 90000), _lap(2, 105000), _lap(3, 140000), _lap(4, 91000)]

    report = await provider.analyze_incidents(laps, _SESSION_INFO)

    assert len(report.incidents) == 2
    severities = {i.lap_number: i.severity for i in report.incidents}
    assert severities[2] == "warning"
    assert severities[3] == "critical"


async def test_base_not_implemented() -> None:
    provider = OpenAIProvider(api_key="fake")

    with pytest.raises(NotImplementedError, match="OpenAIProvider"):
        await provider.analyze_incidents([], _SESSION_INFO)


# ---------------------------------------------------------------------------
# OllamaProvider tests
# ---------------------------------------------------------------------------

_OLLAMA_INCIDENTS_JSON = json.dumps({
    "incidents": [
        {
            "lap_number": 3,
            "severity": "warning",
            "description": "Lap 3 was 15% slower.",
            "root_cause": "Late braking into turn 1.",
            "recommendations": ["Brake earlier into T1"],
        }
    ]
})


def _ollama_response(content: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json={"message": {"role": "assistant", "content": content}},
        request=httpx.Request("POST", "http://test/api/chat"),
    )


async def test_ollama_incidents_success() -> None:
    provider = OllamaProvider(base_url="http://test:11434")
    mock_post = AsyncMock(return_value=_ollama_response(_OLLAMA_INCIDENTS_JSON))
    laps = [_lap(1, 90000, 285.0), _lap(2, 91000, 286.0), _lap(3, 105000, 250.0)]

    with patch.object(provider._client, "post", mock_post):
        report = await provider.analyze_incidents(laps, _SESSION_INFO)

    assert report.provider == "ollama"
    assert len(report.incidents) == 1
    assert report.incidents[0].lap_number == 3
    assert report.incidents[0].severity == "warning"


async def test_ollama_incidents_empty() -> None:
    provider = OllamaProvider(base_url="http://test:11434")
    mock_post = AsyncMock(
        return_value=_ollama_response(json.dumps({"incidents": []}))
    )

    with patch.object(provider._client, "post", mock_post):
        report = await provider.analyze_incidents(
            [_lap(1, 90000), _lap(2, 91000)], _SESSION_INFO
        )

    assert report.incidents == []


async def test_ollama_incidents_json_fallback() -> None:
    provider = OllamaProvider(base_url="http://test:11434")
    mock_post = AsyncMock(return_value=_ollama_response("not json at all"))

    with patch.object(provider._client, "post", mock_post):
        report = await provider.analyze_incidents(
            [_lap(1, 90000)], _SESSION_INFO
        )

    assert len(report.incidents) == 1
    assert report.incidents[0].lap_number == 0
    assert "Could not parse" in report.incidents[0].description


# ---------------------------------------------------------------------------
# ClaudeProvider tests
# ---------------------------------------------------------------------------

def _claude_tool_response(incidents: list[dict]) -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input={"incidents": incidents})
    return SimpleNamespace(content=[tool_block], stop_reason="tool_use")


async def test_claude_incidents_success() -> None:
    provider = ClaudeProvider(api_key="fake")
    mock_create = AsyncMock(return_value=_claude_tool_response([
        {
            "lap_number": 3,
            "severity": "critical",
            "description": "Major slowdown on lap 3.",
            "root_cause": "Spin at turn 5.",
            "recommendations": ["Reduce entry speed at T5"],
        }
    ]))

    with patch.object(provider._client.messages, "create", mock_create):
        report = await provider.analyze_incidents(
            [_lap(1, 90000), _lap(3, 150000)], _SESSION_INFO
        )

    assert report.provider == "claude"
    assert len(report.incidents) == 1
    assert report.incidents[0].severity == "critical"
    assert report.incidents[0].lap_number == 3


async def test_claude_incidents_empty() -> None:
    provider = ClaudeProvider(api_key="fake")
    mock_create = AsyncMock(return_value=_claude_tool_response([]))

    with patch.object(provider._client.messages, "create", mock_create):
        report = await provider.analyze_incidents(
            [_lap(1, 90000), _lap(2, 91000)], _SESSION_INFO
        )

    assert report.provider == "claude"
    assert report.incidents == []
