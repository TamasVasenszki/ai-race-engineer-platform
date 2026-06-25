from fastapi.testclient import TestClient

from main import app


def test_health() -> None:
    # TestClient runs the lifespan, which initializes the AI provider (MockProvider
    # by default). The /health endpoint touches no database, so no DB is required.
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ai_provider": "mock"}
