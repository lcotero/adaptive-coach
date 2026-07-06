"""Tests for completed activities and laps."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain import Activity, ActivityLap, SessionType, SportType


def test_valid_activity_construction_and_serialization() -> None:
    lap = ActivityLap(index=1, distance_m=1000, duration_s=300, avg_hr_bpm=145)
    activity = Activity(
        id="activity-1",
        started_at=datetime(2026, 7, 1, 10, tzinfo=UTC),
        sport_type=SportType.RUNNING,
        session_type=SessionType.EASY,
        duration_s=1800,
        distance_m=6000,
        perceived_effort=4,
        laps=[lap],
    )

    assert activity.laps == (lap,)
    assert activity.model_dump(mode="json")["sport_type"] == "RUNNING"
    assert "labelId" not in Activity.model_fields
    assert "id" in Activity.model_fields


@pytest.mark.parametrize(
    ("model", "kwargs"),
    [
        (ActivityLap, {"index": 1, "duration_s": -1}),
        (ActivityLap, {"index": 0, "duration_s": 1}),
        (ActivityLap, {"index": 1, "duration_s": 1, "avg_hr_bpm": 0}),
    ],
)
def test_invalid_lap_values(model: type[ActivityLap], kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model(**kwargs)


def test_activity_rejects_negative_duration() -> None:
    with pytest.raises(ValidationError):
        Activity(
            id="activity-1",
            started_at=datetime(2026, 7, 1, tzinfo=UTC),
            sport_type=SportType.RUNNING,
            session_type=SessionType.EASY,
            duration_s=-1,
        )
