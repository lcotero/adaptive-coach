"""Request schemas for the public API boundary."""

from pydantic import BaseModel, ConfigDict

from app.coach import LLMCoachDraft, ShadowRecommendation
from app.domain import Activity, AthleteSnapshot, PlannedWorkout
from app.engines import (
    ActivityAnalysis,
    ActivityAnalysisContext,
    AdaptationContext,
    AthleteStateContext,
    SafetyContext,
)


class ActivityAnalysisRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    activity: Activity
    planned_workout: PlannedWorkout | None = None
    context: ActivityAnalysisContext | None = None


class AthleteStateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot: AthleteSnapshot
    recent_analyses: tuple[ActivityAnalysis, ...] = ()
    context: AthleteStateContext | None = None


class ShadowRecommendationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot: AthleteSnapshot
    planned_workout: PlannedWorkout | None = None
    recent_analyses: tuple[ActivityAnalysis, ...] = ()
    athlete_state_context: AthleteStateContext | None = None
    adaptation_context: AdaptationContext | None = None
    safety_context: SafetyContext | None = None


class LLMCoachPromptRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommendation: ShadowRecommendation


class LLMCoachDraftValidationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommendation: ShadowRecommendation
    draft: LLMCoachDraft

