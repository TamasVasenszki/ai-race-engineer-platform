import uuid

from fastapi.testclient import TestClient


def _create_session(client: TestClient) -> str:
    resp = client.post("/sessions/", json={"track": "Monza", "car": "Ferrari 488 GT3"})
    return resp.json()["id"]


def _create_lap(client: TestClient, session_id: str, lap_number: int, lap_time_ms: int) -> None:
    client.post("/laps/", json={
        "session_id": session_id,
        "lap_number": lap_number,
        "lap_time_ms": lap_time_ms,
    })


def test_analyze_incidents_happy_path(client: TestClient) -> None:
    session_id = _create_session(client)
    _create_lap(client, session_id, 1, 90000)
    _create_lap(client, session_id, 2, 91000)
    _create_lap(client, session_id, 3, 92000)

    response = client.post(f"/sessions/{session_id}/incidents")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert isinstance(data["incidents"], list)


def test_analyze_incidents_session_not_found(client: TestClient) -> None:
    fake_id = str(uuid.uuid4())

    response = client.post(f"/sessions/{fake_id}/incidents")

    assert response.status_code == 404


def test_analyze_incidents_no_laps(client: TestClient) -> None:
    session_id = _create_session(client)

    response = client.post(f"/sessions/{session_id}/incidents")

    assert response.status_code == 200
    data = response.json()
    assert data["incidents"] == []


def test_analyze_incidents_detects_critical(client: TestClient) -> None:
    session_id = _create_session(client)
    _create_lap(client, session_id, 1, 90000)
    _create_lap(client, session_id, 2, 140000)

    response = client.post(f"/sessions/{session_id}/incidents")

    assert response.status_code == 200
    data = response.json()
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["severity"] == "critical"
    assert data["incidents"][0]["lap_number"] == 2
