"""Observed recovery metrics."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecoveryState(BaseModel):
    """Recovery observations without readiness inference."""

    model_config = ConfigDict(frozen=True)

    recovery_score: float | None = Field(
        default=None, ge=0, le=100, description="Recovery score on a 0–100 scale"
    )
    hrv_ms: float | None = Field(default=None, gt=0)
    hrv_baseline_ms: float | None = Field(default=None, gt=0)
    resting_hr_bpm: int | None = Field(default=None, gt=0)
    sleep_duration_s: float | None = Field(default=None, ge=0)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: datetime) -> datetime:
        """Require an unambiguous observation time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value
