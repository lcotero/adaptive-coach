"""Observed running-fitness metrics."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunningFitnessState(BaseModel):
    """Running-fitness observations without zones or interpretation."""

    model_config = ConfigDict(frozen=True)

    vo2max: float | None = Field(default=None, gt=0)
    running_level: float | None = Field(default=None, gt=0)
    threshold_pace_s_per_km: float | None = Field(default=None, gt=0)
    threshold_hr_bpm: int | None = Field(default=None, gt=0)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: datetime) -> datetime:
        """Require an unambiguous observation time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value
