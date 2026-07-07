"""Tests for read-only Shadow Coach orchestration."""

from datetime import UTC, date, datetime

from app.coach import (
    RetrospectiveOutcome,
    compare_shadow_recommendation,
    create_shadow_recommendation,
)
from app.domain import (
    Activity,
    AthleteSnapshot,
    IntensityTargetType,
    PlannedWorkout,
    RecoveryState,
    SessionType,
    SportType,
    SubjectiveFeedback,
    TrainingLoadState,
)
from app.engines import (
    ActivityAnalysis,
    AdaptationAction,
    Evidence,
    SafetyContext,
)

OBSERVED_AT = datetime(2026, 7, 7, tzinfo=UTC)


def test_shadow_recommendation_runs_full_read_only_pipeline() -> None:
    recommendation = create_shadow_recommendation(
        snapshot=_snapshot(recovery_score=78, load_ratio=1.2, pain_score=0),
        planned_workout=_workout(SessionType.THRESHOLD),
        recent_analyses=(_analysis(68),),
    )

    assert recommendation.recommended_action is AdaptationAction.REDUCE_INTENSITY
    assert recommendation.planned_workout_id == "workout-1"
    assert recommendation.safety.final_action is AdaptationAction.REDUCE_INTENSITY
    assert _has_code(recommendation.evidence, "SHADOW_READ_ONLY")
    assert _has_code(recommendation.abort_conditions, "PAIN_ABORT_CONDITION")


def test_shadow_recommendation_uses_safety_override() -> None:
    recommendation = create_shadow_recommendation(
        snapshot=_snapshot(recovery_score=80, load_ratio=1.0, pain_score=8),
        planned_workout=_workout(SessionType.EASY),
    )

    assert recommendation.adaptation.action is AdaptationAction.REST
    assert recommendation.safety.final_action is AdaptationAction.REST
    assert recommendation.recommended_action is AdaptationAction.REST


def test_shadow_recommendation_carries_environment_abort_condition() -> None:
    recommendation = create_shadow_recommendation(
        snapshot=_snapshot(recovery_score=80, load_ratio=1.0, pain_score=0),
        planned_workout=_workout(SessionType.EASY),
        safety_context=SafetyContext(environment_warnings=("heat",)),
    )

    assert _has_code(recommendation.abort_conditions, "ENVIRONMENT_ABORT_CONDITION")


def test_retrospective_comparison_marks_easy_replacement_as_followed() -> None:
    recommendation = create_shadow_recommendation(
        snapshot=_snapshot(recovery_score=50, load_ratio=1.35, pain_score=0),
        planned_workout=_workout(SessionType.INTERVAL),
    )
    actual = _activity(SessionType.EASY)

    comparison = compare_shadow_recommendation(
        recommendation,
        actual_activity=actual,
        planned_workout=_workout(SessionType.INTERVAL),
    )

    assert recommendation.recommended_action is AdaptationAction.REPLACE_WITH_EASY
    assert comparison.outcome is RetrospectiveOutcome.FOLLOWED
    assert comparison.actual_session_type is SessionType.EASY


def test_retrospective_comparison_marks_rest_with_activity_as_diverged() -> None:
    recommendation = create_shadow_recommendation(
        snapshot=_snapshot(recovery_score=80, load_ratio=1.0, pain_score=8),
        planned_workout=_workout(SessionType.EASY),
    )

    comparison = compare_shadow_recommendation(
        recommendation,
        actual_activity=_activity(SessionType.EASY),
        planned_workout=_workout(SessionType.EASY),
    )

    assert recommendation.recommended_action is AdaptationAction.REST
    assert comparison.outcome is RetrospectiveOutcome.DIVERGED


def test_retrospective_comparison_marks_rest_without_activity_as_followed() -> None:
    recommendation = create_shadow_recommendation(
        snapshot=_snapshot(recovery_score=80, load_ratio=1.0, pain_score=8),
        planned_workout=_workout(SessionType.EASY),
    )

    comparison = compare_shadow_recommendation(recommendation, actual_activity=None)

    assert comparison.outcome is RetrospectiveOutcome.FOLLOWED
    assert _has_code(comparison.evidence, "NO_ACTIVITY_AFTER_REST")


def _snapshot(recovery_score: float, load_ratio: float, pain_score: int) -> AthleteSnapshot:
    return AthleteSnapshot(
        snapshot_at=OBSERVED_AT,
        training_load=TrainingLoadState(load_ratio=load_ratio, observed_at=OBSERVED_AT),
        recovery=RecoveryState(
            recovery_score=recovery_score,
            hrv_ms=60,
            hrv_baseline_ms=60,
            sleep_duration_s=7 * 3600,
            observed_at=OBSERVED_AT,
        ),
        subjective_feedback=SubjectiveFeedback(recorded_at=OBSERVED_AT, pain_score=pain_score),
    )


def _workout(session_type: SessionType) -> PlannedWorkout:
    return PlannedWorkout(
        id="workout-1",
        scheduled_date=date(2026, 7, 8),
        session_type=session_type,
        title="Planned workout",
        planned_duration_s=3600,
        intensity_target_type=IntensityTargetType.OPEN,
    )


def _analysis(score: float) -> ActivityAnalysis:
    return ActivityAnalysis(
        activity_id="activity-1",
        metrics=(),
        execution_score=score,
        evidence=(Evidence(code="TEST_ANALYSIS", message="Sanitized fixture."),),
    )


def _activity(session_type: SessionType) -> Activity:
    return Activity(
        id="actual-1",
        started_at=OBSERVED_AT,
        sport_type=SportType.RUNNING,
        session_type=session_type,
        duration_s=3600,
        distance_m=8000,
    )


def _has_code(evidence: tuple[Evidence, ...], code: str) -> bool:
    return any(item.code == code for item in evidence)

