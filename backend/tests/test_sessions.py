from fastapi.testclient import TestClient


def test_create_session(client: TestClient) -> None:
    response = client.post("/sessions/", json={"track": "Monza", "car": "Ferrari 488 GT3"})

    assert response.status_code == 201
    data = response.json()
    assert data["track"] == "Monza"
    assert data["car"] == "Ferrari 488 GT3"
    assert "id" in data
    assert "created_at" in data


def test_get_session(client: TestClient) -> None:
    create = client.post("/sessions/", json={"track": "Spa", "car": "Porsche 911 GT3 R"})
    session_id = create.json()["id"]

    response = client.get(f"/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["track"] == "Spa"
    assert response.json()["car"] == "Porsche 911 GT3 R"


def test_get_session_not_found(client: TestClient) -> None:
    response = client.get("/sessions/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_list_sessions(client: TestClient) -> None:
    client.post("/sessions/", json={"track": "Monza", "car": "Ferrari 488 GT3"})
    client.post("/sessions/", json={"track": "Spa", "car": "Porsche 911 GT3 R"})

    response = client.get("/sessions/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    tracks = {s["track"] for s in data}
    assert tracks == {"Monza", "Spa"}


def test_create_session_missing_fields(client: TestClient) -> None:
    response = client.post("/sessions/", json={"track": "Monza"})

    assert response.status_code == 422


def test_list_session_laps(client: TestClient) -> None:
    session = client.post("/sessions/", json={"track": "Monza", "car": "Ferrari 488 GT3"}).json()
    sid = session["id"]
    client.post("/laps/", json={"session_id": sid, "lap_number": 1, "lap_time_ms": 92000})
    client.post("/laps/", json={"session_id": sid, "lap_number": 2, "lap_time_ms": 91500})
    client.post("/laps/", json={"session_id": sid, "lap_number": 3, "lap_time_ms": 91200})

    response = client.get(f"/sessions/{sid}/laps")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [lap["lap_number"] for lap in data] == [1, 2, 3]


def test_list_session_laps_empty(client: TestClient) -> None:
    session = client.post("/sessions/", json={"track": "Spa", "car": "Porsche 911 GT3 R"}).json()

    response = client.get(f"/sessions/{session['id']}/laps")

    assert response.status_code == 200
    assert response.json() == []


def test_list_session_laps_not_found(client: TestClient) -> None:
    response = client.get("/sessions/00000000-0000-0000-0000-000000000000/laps")

    assert response.status_code == 404
