"""Auditable output models for athlete-state assessment."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.engines.analysis_models import Evidence


class ReadinessState(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


class TrainingState(StrEnum):
    RECOVERED = "RECOVERED"
    NORMAL = "NORMAL"
    ACCUMULATING_FATIGUE = "ACCUMULATING_FATIGUE"
    FATIGUED = "FATIGUED"
    OVERREACHED = "OVERREACHED"
    RETURNING = "RETURNING"
    TAPERING = "TAPERING"
    RACE_READY = "RACE_READY"


class AthleteStateContext(BaseModel):
    """Caller-supplied macrocycle context; no phase is inferred from metrics alone."""

    model_config = ConfigDict(frozen=True)

    returning_from_break: bool = False
    tapering: bool = False
    race_within_days: int | None = Field(default=None, ge=0)


class AthleteStateThresholds(BaseModel):
    """Versioned thresholds used by the deterministic athlete-state engine."""

    model_config = ConfigDict(frozen=True)

    version: str = "athlete_state.v1"
    green_min_score: float = 80
    yellow_min_score: float = 60
    orange_min_score: float = 40
    recovery_green_min: float = 75
    recovery_yellow_min: float = 55
    recovery_orange_min: float = 35
    hrv_green_min_ratio: float = 0.95
    hrv_yellow_min_ratio: float = 0.90
    hrv_orange_min_ratio: float = 0.85
    sleep_green_min_hours: float = 7
    sleep_yellow_min_hours: float = 6
    sleep_orange_min_hours: float = 5
    low_load_ratio_max: float = 0.85
    accumulating_load_ratio_min: float = 1.15
    fatigued_load_ratio_min: float = 1.35
    overreached_load_ratio_min: float = 1.50
    poor_execution_score_max: float = 50
    degraded_execution_score_max: float = 70
    pain_red_min: int = 7
    pain_orange_min: int = 4
    stress_orange_min: int = 5
    race_ready_window_days: int = 7


class StateScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float | None
    unit: str
    evidence: tuple[Evidence, ...]


class AthleteStateAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    readiness: ReadinessState
    training_state: TrainingState
    readiness_score: float | None = Field(default=None, ge=0, le=100)
    thresholds_version: str
    scores: tuple[StateScore, ...]
    evidence: tuple[Evidence, ...]

