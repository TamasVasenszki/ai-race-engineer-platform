from fastapi.testclient import TestClient


def test_websocket_connect_disconnect(client: TestClient) -> None:
    with client.websocket_connect("/ws") as ws:
        ws.close()


def test_websocket_receives_new_lap(client: TestClient) -> None:
    session = client.post("/sessions/", json={"track": "Monza", "car": "Ferrari 488 GT3"}).json()

    with client.websocket_connect("/ws") as ws:
        client.post(
            "/laps/",
            json={"session_id": session["id"], "lap_number": 1, "lap_time_ms": 92000},
        )
        msg = ws.receive_json()

    assert msg["type"] == "new_lap"
    assert msg["lap"]["lap_number"] == 1
    assert msg["lap"]["session_id"] == session["id"]


def test_websocket_broadcast_to_multiple_clients(client: TestClient) -> None:
    session = client.post("/sessions/", json={"track": "Spa", "car": "Porsche 911 GT3 R"}).json()

    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2:
        client.post(
            "/laps/",
            json={"session_id": session["id"], "lap_number": 1, "lap_time_ms": 95000},
        )
        msg1 = ws1.receive_json()
        msg2 = ws2.receive_json()

    assert msg1["type"] == "new_lap"
    assert msg2["type"] == "new_lap"
    assert msg1["lap"]["lap_number"] == msg2["lap"]["lap_number"] == 1


def test_websocket_incident_broadcast(client: TestClient) -> None:
    session = client.post("/sessions/", json={"track": "Monza", "car": "Ferrari 488 GT3"}).json()
    sid = session["id"]
    client.post("/laps/", json={"session_id": sid, "lap_number": 1, "lap_time_ms": 90000})
    client.post("/laps/", json={"session_id": sid, "lap_number": 2, "lap_time_ms": 200000})

    with client.websocket_connect("/ws") as ws:
        # Drain the 2 new_lap messages that were broadcast during lap creation
        # (WS was not connected during those POSTs, so nothing to drain here)

        client.post(f"/sessions/{sid}/incidents")

        msg = ws.receive_json()

    assert msg["type"] == "incident_alert"
    assert msg["session_id"] == sid
    assert len(msg["incidents"]) > 0
