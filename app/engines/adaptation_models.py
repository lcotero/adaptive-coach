"""Auditable output models for deterministic workout adaptation."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.engines.analysis_models import Evidence


class AdaptationAction(StrEnum):
    KEEP = "KEEP"
    REDUCE_VOLUME = "REDUCE_VOLUME"
    REDUCE_REPETITIONS = "REDUCE_REPETITIONS"
    REDUCE_INTENSITY = "REDUCE_INTENSITY"
    REPLACE_WITH_EASY = "REPLACE_WITH_EASY"
    RECOVERY_ONLY = "RECOVERY_ONLY"
    REST = "REST"


class AdaptationContext(BaseModel):
    """Caller-supplied planning context; no missed-load compensation is inferred."""

    model_config = ConfigDict(frozen=True)

    phase: str | None = None
    objective: str | None = None
    is_key_session: bool = False
    missed_sessions: int = Field(default=0, ge=0)


class AdaptationThresholds(BaseModel):
    """Versioned thresholds used by the deterministic adaptation engine."""

    model_config = ConfigDict(frozen=True)

    version: str = "adaptation.v1"
    low_confidence_missing_readiness_score: float = 0.55
    normal_confidence: float = 0.75
    high_confidence: float = 0.90
    degraded_execution_score_max: float = 70
    poor_execution_score_max: float = 50


class AdaptationDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: AdaptationAction
    allowed_actions: tuple[AdaptationAction, ...]
    confidence: float = Field(ge=0, le=1)
    thresholds_version: str
    planned_workout_id: str | None = None
    reasons: tuple[Evidence, ...]
    assumptions: tuple[Evidence, ...] = ()

