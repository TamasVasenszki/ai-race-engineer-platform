"""
Assetto Corsa Shared Memory telemetry reader.

Reads real-time telemetry from Assetto Corsa via the Shared Memory API.
WINDOWS ONLY — the mmap tagname format ('Local\\...') is Windows-specific,
and the shared memory only exists while Assetto Corsa is running.

Reference: Assetto Corsa Shared Memory Documentation (Kunos Simulazioni).

Usage:
    with ACTelemetry() as ac:
        if ac.is_connected():
            data = ac.read_lap_payload()
            print(data)
"""

import ctypes
import mmap


# ---------------------------------------------------------------------------
# C struct definitions (ctypes mirrors of the AC shared memory layout)
# Only the fields we actually use are defined precisely; the rest are padded
# so the byte offsets stay correct. Strings in AC are UTF-16 (wchar).
# ---------------------------------------------------------------------------


class SPageFilePhysics(ctypes.Structure):
    """acpmf_physics — real-time physics, updated ~60-333 Hz."""

    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs", ctypes.c_float),
    ]


class SPageFileGraphics(ctypes.Structure):
    """acpmf_graphics — session / lap info."""

    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),          # 0=OFF 1=REPLAY 2=LIVE 3=PAUSE
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("iCurrentTime", ctypes.c_int),    # current lap time in ms
        ("iLastTime", ctypes.c_int),       # last lap time in ms
        ("iBestTime", ctypes.c_int),       # best lap time in ms
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int),
        ("currentSectorIndex", ctypes.c_int),
        ("lastSectorTime", ctypes.c_int),
        ("numberOfLaps", ctypes.c_int),
        ("tyreCompound", ctypes.c_wchar * 33),
    ]


class SPageFileStatic(ctypes.Structure):
    """acpmf_static — static session data, set once."""

    _pack_ = 4
    _fields_ = [
        ("smVersion", ctypes.c_wchar * 15),
        ("acVersion", ctypes.c_wchar * 15),
        ("numberOfSessions", ctypes.c_int),
        ("numCars", ctypes.c_int),
        ("carModel", ctypes.c_wchar * 33),
        ("track", ctypes.c_wchar * 33),
        ("playerName", ctypes.c_wchar * 33),
        ("playerSurname", ctypes.c_wchar * 33),
        ("playerNick", ctypes.c_wchar * 33),
        ("sectorCount", ctypes.c_int),
        ("maxTorque", ctypes.c_float),
        ("maxPower", ctypes.c_float),
        ("maxRpm", ctypes.c_int),
        ("maxFuel", ctypes.c_float),
    ]


# AC graphics status enum
AC_OFF, AC_REPLAY, AC_LIVE, AC_PAUSE = 0, 1, 2, 3


class ACTelemetry:
    """
    Reads Assetto Corsa telemetry from the three shared-memory regions.

    The shared memory only exists while AC is running. Each read returns a
    fresh snapshot — call read_* on whatever cadence you need (e.g. 60 Hz for
    live physics, or once per completed lap for lap payloads).
    """

    # Windows shared-memory tag names exposed by Assetto Corsa.
    _PHYSICS_TAG = "Local\\acpmf_physics"
    _GRAPHICS_TAG = "Local\\acpmf_graphics"
    _STATIC_TAG = "Local\\acpmf_static"

    def __init__(self) -> None:
        self._physics_mm: mmap.mmap | None = None
        self._graphics_mm: mmap.mmap | None = None
        self._static_mm: mmap.mmap | None = None

    # -- lifecycle ----------------------------------------------------------

    def connect(self) -> None:
        """Open the three shared-memory maps. Raises if AC is not running."""
        self._physics_mm = mmap.mmap(
            -1, ctypes.sizeof(SPageFilePhysics), self._PHYSICS_TAG,
            access=mmap.ACCESS_READ,
        )
        self._graphics_mm = mmap.mmap(
            -1, ctypes.sizeof(SPageFileGraphics), self._GRAPHICS_TAG,
            access=mmap.ACCESS_READ,
        )
        self._static_mm = mmap.mmap(
            -1, ctypes.sizeof(SPageFileStatic), self._STATIC_TAG,
            access=mmap.ACCESS_READ,
        )

    def close(self) -> None:
        for mm in (self._physics_mm, self._graphics_mm, self._static_mm):
            if mm is not None:
                mm.close()
        self._physics_mm = self._graphics_mm = self._static_mm = None

    def __enter__(self) -> "ACTelemetry":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- raw reads ----------------------------------------------------------

    def _read(self, mm: mmap.mmap | None, struct_cls):
        if mm is None:
            raise RuntimeError("Not connected. Call connect() first.")
        mm.seek(0)
        return struct_cls.from_buffer_copy(mm.read(ctypes.sizeof(struct_cls)))

    def read_physics(self) -> SPageFilePhysics:
        return self._read(self._physics_mm, SPageFilePhysics)

    def read_graphics(self) -> SPageFileGraphics:
        return self._read(self._graphics_mm, SPageFileGraphics)

    def read_static(self) -> SPageFileStatic:
        return self._read(self._static_mm, SPageFileStatic)

    # -- convenience --------------------------------------------------------

    def is_connected(self) -> bool:
        """True if AC is running and the session is live (not OFF/replay)."""
        if self._graphics_mm is None:
            return False
        try:
            return self.read_graphics().status in (AC_LIVE, AC_PAUSE)
        except (ValueError, OSError):
            return False

    def read_lap_payload(self) -> dict:
        """
        Build a dict matching the backend's POST /laps/ schema (LapCreate):
        session_id is added by the agent, not by AC.
        """
        g = self.read_graphics()
        p = self.read_physics()
        return {
            "lap_number": g.completedLaps,
            "lap_time_ms": g.iLastTime,         # last completed lap, ms
            "sector1_ms": None,                 # AC exposes only last sector
            "sector2_ms": None,                 #   live; full per-sector split
            "sector3_ms": None,                 #   requires accumulating these
            "max_speed_kmh": round(p.speedKmh, 1),
        }

    def read_static_info(self) -> dict:
        """Car/track info for creating a RacingSession."""
        s = self.read_static()
        return {"car": s.carModel, "track": s.track, "max_rpm": s.maxRpm}


if __name__ == "__main__":
    # Quick smoke test — only meaningful on Windows with AC running.
    try:
        with ACTelemetry() as ac:
            if not ac.is_connected():
                print("AC not in a live session (status OFF/REPLAY).")
            else:
                print("Static:", ac.read_static_info())
                print("Lap:   ", ac.read_lap_payload())
    except FileNotFoundError:
        print("Shared memory not found — is Assetto Corsa running? (Windows only)")
