"""Tests for subjective feedback."""

from datetime import UTC, datetime
from typing import Any, cast

import pytest
from pydantic import ValidationError

from app.domain import SubjectiveFeedback


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rpe", 1),
        ("rpe", 10),
        ("pain_score", 0),
        ("pain_score", 10),
        ("sleep_quality", 1),
        ("sleep_quality", 5),
        ("stress_level", 1),
        ("stress_level", 5),
    ],
)
def test_feedback_accepts_scale_boundaries(field: str, value: int) -> None:
    feedback = SubjectiveFeedback(
        recorded_at=datetime(2026, 7, 1, tzinfo=UTC),
        **cast(Any, {field: value}),
    )
    assert getattr(feedback, field) == value


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rpe", 0),
        ("rpe", 11),
        ("pain_score", -1),
        ("pain_score", 11),
        ("sleep_quality", 0),
        ("sleep_quality", 6),
        ("stress_level", 0),
        ("stress_level", 6),
    ],
)
def test_feedback_rejects_values_outside_scales(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        SubjectiveFeedback(
            recorded_at=datetime(2026, 7, 1, tzinfo=UTC),
            **cast(Any, {field: value}),
        )
