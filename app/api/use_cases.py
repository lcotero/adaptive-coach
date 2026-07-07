"""Application use cases exposed by the API layer."""

from app.coach import (
    LLMCoachDraft,
    LLMCoachResponse,
    ShadowRecommendation,
    create_shadow_recommendation,
    validate_llm_coach_draft,
)
from app.coach.llm_coach import build_llm_coach_prompt
from app.coach.llm_models import LLMCoachPrompt
from app.domain import Activity, AthleteSnapshot, PlannedWorkout
from app.engines import (
    ActivityAnalysis,
    ActivityAnalysisContext,
    AdaptationContext,
    AthleteStateAssessment,
    AthleteStateContext,
    SafetyContext,
    analyze_activity,
    assess_athlete_state,
)


def analyze_completed_activity(
    activity: Activity,
    planned_workout: PlannedWorkout | None = None,
    context: ActivityAnalysisContext | None = None,
) -> ActivityAnalysis:
    """Analyze a completed activity using deterministic rules."""
    return analyze_activity(activity, planned_workout, context)


def assess_snapshot_state(
    snapshot: AthleteSnapshot,
    recent_analyses: tuple[ActivityAnalysis, ...] = (),
    context: AthleteStateContext | None = None,
) -> AthleteStateAssessment:
    """Assess daily readiness and longer-term training state."""
    return assess_athlete_state(snapshot, recent_analyses, context)


def create_shadow_recommendation_use_case(
    snapshot: AthleteSnapshot,
    planned_workout: PlannedWorkout | None = None,
    recent_analyses: tuple[ActivityAnalysis, ...] = (),
    athlete_state_context: AthleteStateContext | None = None,
    adaptation_context: AdaptationContext | None = None,
    safety_context: SafetyContext | None = None,
) -> ShadowRecommendation:
    """Create a read-only Shadow Coach recommendation."""
    return create_shadow_recommendation(
        snapshot=snapshot,
        planned_workout=planned_workout,
        recent_analyses=recent_analyses,
        athlete_state_context=athlete_state_context,
        adaptation_context=adaptation_context,
        safety_context=safety_context,
    )


def build_llm_prompt_use_case(recommendation: ShadowRecommendation) -> LLMCoachPrompt:
    """Build the bounded LLM prompt for inspection or external provider use."""
    return build_llm_coach_prompt(recommendation)


def validate_llm_draft_use_case(
    recommendation: ShadowRecommendation,
    draft: LLMCoachDraft,
) -> LLMCoachResponse:
    """Validate an LLM draft against deterministic recommendation boundaries."""
    return validate_llm_coach_draft(recommendation, draft)

