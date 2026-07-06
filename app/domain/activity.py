"""Normalized completed activities and their laps."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import SessionType, SportType


def _require_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value


class ActivityLap(BaseModel):
    """A normalized lap or segment from a completed activity."""

    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=1)
    distance_m: float | None = Field(default=None, ge=0)
    duration_s: float = Field(gt=0)
    avg_pace_s_per_km: float | None = Field(default=None, gt=0)
    avg_hr_bpm: int | None = Field(default=None, gt=0)
    max_hr_bpm: int | None = Field(default=None, gt=0)
    avg_cadence_spm: float | None = Field(default=None, ge=0)
    avg_power_w: float | None = Field(default=None, ge=0)
    elevation_gain_m: float | None = Field(default=None, ge=0)
    elevation_loss_m: float | None = Field(default=None, ge=0)


class Activity(BaseModel):
    """A provider-independent completed activity."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    started_at: datetime
    sport_type: SportType
    session_type: SessionType
    title: str | None = None
    duration_s: float = Field(gt=0)
    distance_m: float | None = Field(default=None, ge=0)
    avg_pace_s_per_km: float | None = Field(default=None, gt=0)
    avg_hr_bpm: int | None = Field(default=None, gt=0)
    max_hr_bpm: int | None = Field(default=None, gt=0)
    avg_cadence_spm: float | None = Field(default=None, ge=0)
    elevation_gain_m: float | None = Field(default=None, ge=0)
    elevation_loss_m: float | None = Field(default=None, ge=0)
    training_load: float | None = Field(default=None, ge=0)
    aerobic_training_effect: float | None = Field(default=None, ge=0)
    anaerobic_training_effect: float | None = Field(default=None, ge=0)
    perceived_effort: int | None = Field(
        default=None, ge=1, le=10, description="Session RPE on a 1–10 scale"
    )
    laps: tuple[ActivityLap, ...] = ()

    _validate_started_at = field_validator("started_at")(_require_aware)
