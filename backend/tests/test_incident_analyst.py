import pytest

from ai.mock import MockProvider
from ai.openai import OpenAIProvider

_SESSION_INFO = {"track": "Monza", "car": "Ferrari 488 GT3"}


def _lap(number: int, time_ms: int) -> dict:
    return {"lap_number": number, "lap_time_ms": time_ms}


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
