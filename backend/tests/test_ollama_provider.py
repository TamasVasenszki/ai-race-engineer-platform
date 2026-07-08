from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ai.ollama import OllamaProvider

_LAP_DATA = {
    "lap_number": 5,
    "lap_time_ms": 95200,
    "sector1_ms": 31000,
    "sector2_ms": 33200,
    "sector3_ms": 31000,
    "max_speed_kmh": 285.5,
}

_VALID_JSON = json.dumps({
    "summary": "Good lap with consistent sector times.",
    "recommendations": ["Brake later into T1", "Use more kerb at T6 exit"],
})


def _ollama_response(content: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json={"message": {"role": "assistant", "content": content}},
        request=httpx.Request("POST", "http://test/api/chat"),
    )


@pytest.fixture()
def provider() -> OllamaProvider:
    return OllamaProvider(base_url="http://test:11434", model="llama3.2")


async def test_analyze_lap_success(provider: OllamaProvider) -> None:
    mock_post = AsyncMock(return_value=_ollama_response(_VALID_JSON))
    with patch.object(provider._client, "post", mock_post):
        result = await provider.analyze_lap(_LAP_DATA)

    assert result.summary == "Good lap with consistent sector times."
    assert result.recommendations == ["Brake later into T1", "Use more kerb at T6 exit"]
    assert result.provider == "ollama"
    mock_post.assert_called_once()


async def test_analyze_lap_json_retry_succeeds(provider: OllamaProvider) -> None:
    mock_post = AsyncMock(side_effect=[
        _ollama_response("not valid json"),
        _ollama_response(_VALID_JSON),
    ])
    with patch.object(provider._client, "post", mock_post):
        result = await provider.analyze_lap(_LAP_DATA)

    assert result.summary == "Good lap with consistent sector times."
    assert result.provider == "ollama"
    assert mock_post.call_count == 2


async def test_analyze_lap_json_fallback(provider: OllamaProvider) -> None:
    mock_post = AsyncMock(return_value=_ollama_response("just plain text, no json"))
    with patch.object(provider._client, "post", mock_post):
        result = await provider.analyze_lap(_LAP_DATA)

    assert result.summary == "just plain text, no json"
    assert result.recommendations == ["JSON parsing failed — raw response returned as summary"]
    assert result.provider == "ollama"


async def test_analyze_lap_connection_error(provider: OllamaProvider) -> None:
    mock_post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    with patch.object(provider._client, "post", mock_post):
        with pytest.raises(RuntimeError, match="cannot connect to Ollama"):
            await provider.analyze_lap(_LAP_DATA)


async def test_analyze_lap_model_not_found(provider: OllamaProvider) -> None:
    mock_post = AsyncMock(return_value=_ollama_response("", status_code=404))
    with patch.object(provider._client, "post", mock_post):
        with pytest.raises(RuntimeError, match="model 'llama3.2' not found"):
            await provider.analyze_lap(_LAP_DATA)
