"""Read-only Shadow Coach orchestration."""

from app.coach.shadow_models import (
    RetrospectiveComparison,
    RetrospectiveOutcome,
    ShadowRecommendation,
)
from app.domain import Activity, AthleteSnapshot, PlannedWorkout, SessionType
from app.engines import (
    ActivityAnalysis,
    AdaptationContext,
    AthleteStateAssessment,
    AthleteStateContext,
    Evidence,
    SafetyContext,
    SafetyDecision,
    SafetyStatus,
    analyze_activity,
    assess_athlete_state,
    select_adaptation,
    validate_safety,
)
from app.engines.adaptation_models import AdaptationAction


def create_shadow_recommendation(
    snapshot: AthleteSnapshot,
    planned_workout: PlannedWorkout | None = None,
    recent_analyses: tuple[ActivityAnalysis, ...] = (),
    athlete_state_context: AthleteStateContext | None = None,
    adaptation_context: AdaptationContext | None = None,
    safety_context: SafetyContext | None = None,
) -> ShadowRecommendation:
    """Create a read-only recommendation using deterministic engines only."""
    athlete_state = assess_athlete_state(
        snapshot=snapshot,
        recent_analyses=recent_analyses,
        context=athlete_state_context,
    )
    adaptation = select_adaptation(
        athlete_state=athlete_state,
        planned_workout=planned_workout,
        recent_analyses=recent_analyses,
        context=adaptation_context,
    )
    safety = validate_safety(
        adaptation=adaptation,
        athlete_state=athlete_state,
        snapshot=snapshot,
        planned_workout=planned_workout,
        context=safety_context,
    )
    evidence = (
        Evidence(
            code="SHADOW_READ_ONLY",
            message="Recommendation is read-only and does not modify COROS or calendars.",
        ),
        Evidence(
            code="DETERMINISTIC_PIPELINE",
            message="Built from athlete-state, adaptation and safety engines.",
        ),
    )
    return ShadowRecommendation(
        planned_workout_id=planned_workout.id if planned_workout is not None else None,
        recommended_action=safety.final_action,
        confidence=safety.confidence,
        athlete_state=athlete_state,
        adaptation=adaptation,
        safety=safety,
        evidence=evidence,
        assumptions=adaptation.assumptions,
        uncertainty=_uncertainty(athlete_state, safety),
        abort_conditions=_abort_conditions(safety_context),
    )


def compare_shadow_recommendation(
    recommendation: ShadowRecommendation,
    actual_activity: Activity | None,
    planned_workout: PlannedWorkout | None = None,
) -> RetrospectiveComparison:
    """Compare a shadow recommendation with later observed athlete behavior."""
    if actual_activity is None:
        return _compare_missing_actual(recommendation)

    actual_analysis = analyze_activity(actual_activity, planned_workout)
    outcome = _classify_retrospective_outcome(
        action=recommendation.recommended_action,
        actual_session_type=actual_activity.session_type,
        planned_session_type=planned_workout.session_type if planned_workout is not None else None,
    )
    return RetrospectiveComparison(
        outcome=outcome,
        recommended_action=recommendation.recommended_action,
        actual_session_type=actual_activity.session_type,
        evidence=(
            Evidence(
                code="ACTUAL_ACTIVITY_OBSERVED",
                message="Compared recommendation with the later observed activity.",
            ),
            Evidence(
                code="ACTUAL_EXECUTION_SCORE",
                message=(
                    "Actual activity was analyzed for audit context; no causal explanation "
                    "is inferred."
                ),
            ),
            *actual_analysis.evidence,
        ),
    )


def _compare_missing_actual(recommendation: ShadowRecommendation) -> RetrospectiveComparison:
    if recommendation.recommended_action is AdaptationAction.REST:
        return RetrospectiveComparison(
            outcome=RetrospectiveOutcome.FOLLOWED,
            recommended_action=recommendation.recommended_action,
            evidence=(
                Evidence(code="NO_ACTIVITY_AFTER_REST", message="No activity followed REST."),
            ),
        )
    return RetrospectiveComparison(
        outcome=RetrospectiveOutcome.NOT_EVALUATED,
        recommended_action=recommendation.recommended_action,
        evidence=(Evidence(code="NO_ACTUAL_ACTIVITY", message="No later activity was provided."),),
    )


def _classify_retrospective_outcome(
    action: AdaptationAction,
    actual_session_type: SessionType,
    planned_session_type: SessionType | None,
) -> RetrospectiveOutcome:
    if action is AdaptationAction.REST:
        return RetrospectiveOutcome.DIVERGED
    if action in {AdaptationAction.RECOVERY_ONLY, AdaptationAction.REPLACE_WITH_EASY}:
        return (
            RetrospectiveOutcome.FOLLOWED
            if actual_session_type in {SessionType.RECOVERY, SessionType.EASY}
            else RetrospectiveOutcome.DIVERGED
        )
    if action is AdaptationAction.KEEP and planned_session_type is not None:
        return (
            RetrospectiveOutcome.FOLLOWED
            if actual_session_type == planned_session_type
            else RetrospectiveOutcome.DIVERGED
        )
    return RetrospectiveOutcome.NOT_EVALUATED


def _uncertainty(
    athlete_state: AthleteStateAssessment,
    safety: SafetyDecision,
) -> tuple[Evidence, ...]:
    uncertainty: list[Evidence] = []
    if athlete_state.readiness_score is None:
        uncertainty.append(
            Evidence(
                code="MISSING_READINESS_SCORE",
                message="Readiness score is unavailable; confidence depends on safety caps.",
            )
        )
    if safety.status is SafetyStatus.APPROVED:
        uncertainty.extend(safety.warnings)
    return tuple(uncertainty)


def _abort_conditions(context: SafetyContext | None) -> tuple[Evidence, ...]:
    conditions = [
        Evidence(
            code="PAIN_ABORT_CONDITION",
            message="Stop or downgrade if pain appears or increases during the session.",
        ),
        Evidence(
            code="MEDICAL_ABORT_CONDITION",
            message="Stop and seek professional evaluation for medical warning symptoms.",
        ),
    ]
    if context is not None and context.environment_warnings:
        conditions.append(
            Evidence(
                code="ENVIRONMENT_ABORT_CONDITION",
                message="Downgrade or stop if environmental warning conditions worsen.",
            )
        )
    return tuple(conditions)
