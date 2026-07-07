"""Read-only Shadow Coach output models."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain import SessionType
from app.engines import (
    AdaptationAction,
    AdaptationDecision,
    AthleteStateAssessment,
    Evidence,
    SafetyDecision,
)


class RetrospectiveOutcome(StrEnum):
    FOLLOWED = "FOLLOWED"
    DIVERGED = "DIVERGED"
    NOT_EVALUATED = "NOT_EVALUATED"


class ShadowRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    planned_workout_id: str | None
    recommended_action: AdaptationAction
    confidence: float = Field(ge=0, le=1)
    athlete_state: AthleteStateAssessment
    adaptation: AdaptationDecision
    safety: SafetyDecision
    evidence: tuple[Evidence, ...]
    assumptions: tuple[Evidence, ...]
    uncertainty: tuple[Evidence, ...]
    abort_conditions: tuple[Evidence, ...]


class RetrospectiveComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    outcome: RetrospectiveOutcome
    recommended_action: AdaptationAction
    actual_session_type: SessionType | None = None
    evidence: tuple[Evidence, ...]

