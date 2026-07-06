"""Tests for aggregate athlete snapshots."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.domain import (
    Activity,
    AthleteSnapshot,
    IntensityTargetType,
    PlannedWorkout,
    RecoveryState,
    SessionType,
    SportType,
    TrainingLoadState,
)


def test_snapshot_accepts_missing_optional_state() -> None:
    snapshot = AthleteSnapshot(snapshot_at=datetime(2026, 7, 1, tzinfo=UTC))
    assert snapshot.recent_activities == ()
    assert snapshot.recovery is None


def test_snapshot_aggregates_nested_models() -> None:
    observed_at = datetime(2026, 7, 1, tzinfo=UTC)
    activity = Activity(
        id="activity-1",
        started_at=observed_at,
        sport_type=SportType.RUNNING,
        session_type=SessionType.EASY,
        duration_s=1800,
    )
    snapshot = AthleteSnapshot(
        snapshot_at=observed_at,
        recent_activities=[activity],
        training_load=TrainingLoadState(short_term_load=300, observed_at=observed_at),
        recovery=RecoveryState(recovery_score=75, observed_at=observed_at),
        planned_workout=PlannedWorkout(
            id="workout-1",
            scheduled_date=date(2026, 7, 2),
            session_type=SessionType.EASY,
            title="Easy run",
            intensity_target_type=IntensityTargetType.OPEN,
        ),
    )
    assert snapshot.recent_activities == (activity,)
    assert snapshot.recovery is not None


def test_snapshot_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError):
        AthleteSnapshot(snapshot_at=datetime(2026, 7, 1))
