"""Tests for recovery observations."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain import RecoveryState


@pytest.mark.parametrize(
    ("field", "value"),
    [("hrv_ms", 0), ("resting_hr_bpm", 0), ("sleep_duration_s", -1)],
)
def test_recovery_rejects_invalid_values(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        RecoveryState(observed_at=datetime(2026, 7, 1, tzinfo=UTC), **{field: value})


def test_recovery_score_scale_is_enforced() -> None:
    with pytest.raises(ValidationError):
        RecoveryState(recovery_score=101, observed_at=datetime(2026, 7, 1, tzinfo=UTC))
