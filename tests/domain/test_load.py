"""Tests for training-load state."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain import TrainingLoadState


def test_training_load_state_preserves_observed_values() -> None:
    state = TrainingLoadState(
        short_term_load=420,
        long_term_load=390,
        load_ratio=1.08,
        observed_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    assert state.load_ratio == 1.08


def test_training_load_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        TrainingLoadState(short_term_load=-1, observed_at=datetime(2026, 7, 1, tzinfo=UTC))
