"""Tests using sanitized COROS-shaped payloads."""

from datetime import UTC, datetime

import pytest

from app.domain import SessionType, SportType
from app.integrations.coros import (
    CorosActivityDTO,
    CorosLapPayloadDTO,
    CorosMappingError,
    map_activity,
    map_lap_payload,
)


def test_activity_mapping_is_provider_neutral() -> None:
    dto = CorosActivityDTO.model_validate(
        {
            "label_id": "sanitized-42",
            "started_at": "2026-07-01T10:00:00Z",
            "sport_code": 100,
            "session_label": "easy",
            "duration_s": 1800,
            "distance_m": 6000,
            "unknown_provider_field": "ignored",
            "laps": [{"index": 1, "duration_s": 300, "distance_m": 1000}],
        }
    )
    activity = map_activity(dto, {100: SportType.RUNNING})

    assert activity.id == "sanitized-42"
    assert activity.session_type is SessionType.EASY
    assert activity.laps[0].distance_m == 1000
    assert "label_id" not in type(activity).model_fields


def test_missing_optional_metrics_remain_none() -> None:
    activity = map_activity(
        CorosActivityDTO(
            label_id="sanitized-43",
            started_at=datetime(2026, 7, 1, tzinfo=UTC),
            sport_code=100,
            duration_s=1200,
        ),
        {100: SportType.RUNNING},
    )
    assert activity.avg_hr_bpm is None
    assert activity.distance_m is None


def test_unknown_sport_code_is_explicit_error() -> None:
    dto = CorosActivityDTO(
        label_id="sanitized-44",
        started_at=datetime(2026, 7, 1, tzinfo=UTC),
        sport_code=999,
        duration_s=1200,
    )
    with pytest.raises(CorosMappingError, match="999"):
        map_activity(dto, {})


def test_verified_coros_lap_units_are_normalized() -> None:
    payload = CorosLapPayloadDTO.model_validate(
        {
            "lapIndex": 2,
            "distance": 100000,
            "time": 381.74,
            "avgPace": 381.75,
            "avgHr": 144,
            "maxHr": 149,
            "avgCadence": 160,
            "avgPower": 236,
            "elevGain": 4,
            "totalDescent": 13,
        }
    )
    lap = map_lap_payload(payload)

    assert lap.distance_m == 1000
    assert lap.duration_s == 381.74
