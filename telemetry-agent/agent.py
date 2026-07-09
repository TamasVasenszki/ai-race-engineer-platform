"""
Assetto Corsa Telemetry Agent

Polls the AC shared memory every few seconds, detects newly completed laps,
and POSTs them to the backend API. Runs on the Windows PC where AC is running.

Usage:
    python agent.py                          # default: localhost backend
    python agent.py --backend http://192.168.1.42:8000  # Mac on LAN
    python agent.py --interval 3             # poll every 3 seconds (default)
"""

import argparse
import time

import httpx

from ac_telemetry import ACTelemetry


def create_session(client: httpx.Client, backend: str, car: str, track: str) -> str:
    """Create a RacingSession via the backend API. Returns the session UUID."""
    resp = client.post(f"{backend}/sessions/", json={"track": track, "car": car})
    resp.raise_for_status()
    session_id = resp.json()["id"]
    print(f"[agent] Created session {session_id} (car={car}, track={track})")
    return session_id


def post_lap(client: httpx.Client, backend: str, session_id: str, lap_data: dict) -> None:
    """POST a completed lap to the backend. Retries once after 5s on failure."""
    payload = {
        "session_id": session_id,
        **lap_data,
    }
    for attempt in range(2):
        try:
            resp = client.post(f"{backend}/laps/", json=payload)
            if resp.status_code == 201:
                data = resp.json()
                print(f"[agent] Lap {data['lap_number']} saved — "
                      f"time: {data['lap_time_ms']}ms — "
                      f"AI: {data.get('ai_summary', 'N/A')}")
                return
            print(f"[agent] ERROR: backend returned {resp.status_code}: {resp.text}")
        except httpx.HTTPError as exc:
            print(f"[agent] ERROR: {exc}")
        if attempt == 0:
            print("[agent] Retrying in 5s...")
            time.sleep(5)
    print("[agent] POST failed after 2 attempts, skipping lap.")


def main() -> None:
    parser = argparse.ArgumentParser(description="AC Telemetry Agent")
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Polling interval in seconds (default: 3)",
    )
    args = parser.parse_args()

    print(f"[agent] Connecting to Assetto Corsa shared memory...")

    try:
        ac = ACTelemetry()
        ac.connect()
    except FileNotFoundError:
        print("[agent] ERROR: AC shared memory not found.")
        print("[agent] Make sure Assetto Corsa is running and you are in a session.")
        return

    if not ac.is_connected():
        print("[agent] WARNING: AC is running but not in a live session.")
        print("[agent] Start a practice/race session, then restart this agent.")
        ac.close()
        return

    # Read static info (car, track)
    static = ac.read_static_info()
    print(f"[agent] Connected! Car: {static['car']}, Track: {static['track']}")

    # Create a backend session
    client = httpx.Client(timeout=30.0)
    session_id = create_session(client, args.backend, static["car"], static["track"])

    # Main polling loop
    last_completed_laps = ac.read_graphics().completedLaps
    print(f"[agent] Polling every {args.interval}s — waiting for completed laps...")
    print(f"[agent] (Already completed: {last_completed_laps} laps)")
    print()

    try:
        while True:
            time.sleep(args.interval)

            if not ac.is_connected():
                print("[agent] AC session ended or paused. Waiting...")
                continue

            g = ac.read_graphics()

            # Detect new lap completion
            if g.completedLaps > last_completed_laps:
                lap_data = ac.read_lap_payload()
                print(f"[agent] New lap detected! Lap {g.completedLaps}, "
                      f"time: {g.iLastTime}ms")
                post_lap(client, args.backend, session_id, lap_data)
                last_completed_laps = g.completedLaps

    except KeyboardInterrupt:
        print("\n[agent] Stopped by user.")
    finally:
        ac.close()
        client.close()
        print("[agent] Bye!")


if __name__ == "__main__":
    main()
