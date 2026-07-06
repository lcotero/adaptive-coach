"""Tests for planned workouts."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.domain import IntensityTargetType, PlannedWorkout, SessionType


def test_workout_accepts_ordered_targets() -> None:
    workout = PlannedWorkout(
        id="workout-1",
        scheduled_date=date(2026, 7, 7),
        session_type=SessionType.TEMPO,
        title="Tempo",
        planned_duration_s=3600,
        intensity_target_type=IntensityTargetType.PACE,
        target_min=270,
        target_max=285,
    )
    assert workout.target_min == 270


def test_workout_rejects_inverted_targets() -> None:
    with pytest.raises(ValidationError):
        PlannedWorkout(
            id="workout-1",
            scheduled_date=date(2026, 7, 7),
            session_type=SessionType.TEMPO,
            title="Tempo",
            intensity_target_type=IntensityTargetType.PACE,
            target_min=300,
            target_max=280,
        )


def test_workout_rejects_negative_duration() -> None:
    with pytest.raises(ValidationError):
        PlannedWorkout(
            id="workout-1",
            scheduled_date=date(2026, 7, 7),
            session_type=SessionType.EASY,
            title="Easy",
            planned_duration_s=-1,
            intensity_target_type=IntensityTargetType.OPEN,
        )
