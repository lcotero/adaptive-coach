"""Boundary DTOs for sanitized COROS-shaped data."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CorosDTO(BaseModel):
    """Base configuration for external payload DTOs."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class CorosActivityLapDTO(CorosDTO):
    """External lap values before domain normalization."""

    index: int
    distance_m: float | None = None
    duration_s: float
    avg_pace_s_per_km: float | None = None
    avg_hr_bpm: int | None = None
    max_hr_bpm: int | None = None
    avg_cadence_spm: float | None = None
    avg_power_w: float | None = None
    elevation_gain_m: float | None = None
    elevation_loss_m: float | None = None


class CorosLapPayloadDTO(CorosDTO):
    """Raw fields verified in the COROS activity-lap response."""

    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)

    lap_index: int = Field(alias="lapIndex")
    distance_centimeters: float = Field(alias="distance")
    duration_s: float = Field(alias="time")
    avg_pace_s_per_km: float | None = Field(default=None, alias="avgPace")
    avg_hr_bpm: int | None = Field(default=None, alias="avgHr")
    max_hr_bpm: int | None = Field(default=None, alias="maxHr")
    avg_cadence_spm: float | None = Field(default=None, alias="avgCadence")
    avg_power_w: float | None = Field(default=None, alias="avgPower")
    elevation_gain_m: float | None = Field(default=None, alias="elevGain")
    elevation_loss_m: float | None = Field(default=None, alias="totalDescent")


class CorosActivityDTO(CorosDTO):
    """External activity data; provider identifiers remain at this boundary."""

    label_id: str
    started_at: datetime
    sport_code: int
    session_label: str | None = None
    title: str | None = None
    duration_s: float
    distance_m: float | None = None
    avg_pace_s_per_km: float | None = None
    avg_hr_bpm: int | None = None
    max_hr_bpm: int | None = None
    avg_cadence_spm: float | None = None
    elevation_gain_m: float | None = None
    elevation_loss_m: float | None = None
    training_load: float | None = None
    aerobic_training_effect: float | None = None
    anaerobic_training_effect: float | None = None
    perceived_effort: int | None = None
    laps: tuple[CorosActivityLapDTO, ...] = ()


class CorosTrainingLoadDTO(CorosDTO):
    short_term_load: float | None = None
    long_term_load: float | None = None
    load_ratio: float | None = None
    observed_at: datetime


class CorosRecoveryDTO(CorosDTO):
    recovery_score: float | None = None
    hrv_ms: float | None = None
    hrv_baseline_ms: float | None = None
    resting_hr_bpm: int | None = None
    sleep_duration_s: float | None = None
    observed_at: datetime


class CorosFitnessDTO(CorosDTO):
    vo2max: float | None = None
    running_level: float | None = None
    threshold_pace_s_per_km: float | None = None
    threshold_hr_bpm: int | None = None
    observed_at: datetime


class CorosWorkoutDTO(CorosDTO):
    workout_id: str
    scheduled_date: date
    session_label: str | None = None
    title: str
    planned_duration_s: float | None = None
    planned_distance_m: float | None = None
    intensity_label: str | None = None
    target_min: float | None = None
    target_max: float | None = None
    notes: str | None = None
