from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from ai.ollama import OllamaProvider
from main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ai_provider": "mock"}


def test_health_ollama_reachable() -> None:
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None

    provider = OllamaProvider(base_url="http://test:11434")

    with (
        patch("main.get_provider", return_value=provider),
        patch("main.settings.ai_provider", "ollama"),
        patch("main.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ai_provider"] == "ollama"
    assert data["ollama_status"] == "ok"


def test_health_ollama_unreachable() -> None:
    provider = OllamaProvider(base_url="http://test:11434")

    with (
        patch("main.get_provider", return_value=provider),
        patch("main.settings.ai_provider", "ollama"),
        patch("main.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ai_provider"] == "ollama"
    assert data["ollama_status"] == "unreachable"
