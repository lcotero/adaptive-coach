"""FastAPI application for Adaptive Coach."""

from fastapi import FastAPI

from app.api.schemas import (
    ActivityAnalysisRequest,
    AthleteStateRequest,
    LLMCoachDraftValidationRequest,
    LLMCoachPromptRequest,
    ShadowRecommendationRequest,
)
from app.api.use_cases import (
    analyze_completed_activity,
    assess_snapshot_state,
    build_llm_prompt_use_case,
    create_shadow_recommendation_use_case,
    validate_llm_draft_use_case,
)
from app.coach import LLMCoachPrompt, LLMCoachResponse, ShadowRecommendation
from app.engines import ActivityAnalysis, AthleteStateAssessment

app = FastAPI(
    title="Adaptive Coach",
    version="0.1.0",
    description="Read-only adaptive running coach API.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}


@app.post("/activity-analysis", response_model=ActivityAnalysis)
def activity_analysis(request: ActivityAnalysisRequest) -> ActivityAnalysis:
    """Analyze one completed activity."""
    return analyze_completed_activity(
        activity=request.activity,
        planned_workout=request.planned_workout,
        context=request.context,
    )


@app.post("/athlete-state", response_model=AthleteStateAssessment)
def athlete_state(request: AthleteStateRequest) -> AthleteStateAssessment:
    """Assess readiness and training state from a snapshot."""
    return assess_snapshot_state(
        snapshot=request.snapshot,
        recent_analyses=request.recent_analyses,
        context=request.context,
    )


@app.post("/shadow-recommendation", response_model=ShadowRecommendation)
def shadow_recommendation(request: ShadowRecommendationRequest) -> ShadowRecommendation:
    """Create a read-only Shadow Coach recommendation."""
    return create_shadow_recommendation_use_case(
        snapshot=request.snapshot,
        planned_workout=request.planned_workout,
        recent_analyses=request.recent_analyses,
        athlete_state_context=request.athlete_state_context,
        adaptation_context=request.adaptation_context,
        safety_context=request.safety_context,
    )


@app.post("/llm-coach-prompt", response_model=LLMCoachPrompt)
def llm_coach_prompt(request: LLMCoachPromptRequest) -> LLMCoachPrompt:
    """Build a bounded prompt for an external LLM provider."""
    return build_llm_prompt_use_case(request.recommendation)


@app.post("/llm-coach-response", response_model=LLMCoachResponse)
def llm_coach_response(request: LLMCoachDraftValidationRequest) -> LLMCoachResponse:
    """Validate a generated LLM draft before surfacing it."""
    return validate_llm_draft_use_case(request.recommendation, request.draft)

