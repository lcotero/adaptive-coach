"""Tests for final deterministic safety validation."""

from datetime import UTC, date, datetime

from app.domain import (
    AthleteSnapshot,
    IntensityTargetType,
    PlannedWorkout,
    SessionType,
    SubjectiveFeedback,
)
from app.engines import (
    AdaptationAction,
    AdaptationDecision,
    AthleteStateAssessment,
    Evidence,
    ReadinessState,
    SafetyContext,
    SafetyStatus,
    TrainingState,
    validate_safety,
)

OBSERVED_AT = datetime(2026, 7, 7, tzinfo=UTC)


def test_medical_warning_blocks_recommendation() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.KEEP),
        _state(ReadinessState.GREEN, TrainingState.NORMAL, readiness_score=90),
        snapshot=_snapshot(pain_score=0),
        planned_workout=_workout(SessionType.EASY),
        context=SafetyContext(medical_warning_signals=("chest_pain",)),
    )

    assert decision.status is SafetyStatus.BLOCKED
    assert decision.final_action is AdaptationAction.REST
    assert _has_code(decision.reasons, "MEDICAL_WARNING_SIGNAL")


def test_high_pain_blocks_training() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.REPLACE_WITH_EASY),
        _state(ReadinessState.YELLOW, TrainingState.NORMAL, readiness_score=65),
        snapshot=_snapshot(pain_score=8),
        planned_workout=_workout(SessionType.EASY),
    )

    assert decision.status is SafetyStatus.BLOCKED
    assert decision.original_action is AdaptationAction.REPLACE_WITH_EASY
    assert decision.final_action is AdaptationAction.REST


def test_moderate_pain_overrides_to_recovery_only() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.REDUCE_VOLUME),
        _state(ReadinessState.YELLOW, TrainingState.NORMAL, readiness_score=70),
        snapshot=_snapshot(pain_score=4),
        planned_workout=_workout(SessionType.LONG_RUN),
    )

    assert decision.status is SafetyStatus.MODIFIED
    assert decision.final_action is AdaptationAction.RECOVERY_ONLY
    assert decision.confidence == 0.70


def test_unsafe_quality_intensity_is_replaced_with_easy() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.KEEP),
        _state(ReadinessState.ORANGE, TrainingState.ACCUMULATING_FATIGUE, readiness_score=45),
        snapshot=_snapshot(pain_score=0),
        planned_workout=_workout(SessionType.INTERVAL),
    )

    assert decision.status is SafetyStatus.MODIFIED
    assert decision.final_action is AdaptationAction.REPLACE_WITH_EASY
    assert _has_code(decision.reasons, "SAFETY_OVERRIDE")


def test_overreached_state_prevents_less_conservative_action() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.REDUCE_INTENSITY),
        _state(ReadinessState.YELLOW, TrainingState.OVERREACHED, readiness_score=62),
        snapshot=_snapshot(pain_score=0),
        planned_workout=_workout(SessionType.TEMPO),
    )

    assert decision.status is SafetyStatus.MODIFIED
    assert decision.final_action is AdaptationAction.RECOVERY_ONLY


def test_missing_data_caps_confidence_but_keeps_allowed_action() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.KEEP, confidence=0.75),
        _state(ReadinessState.YELLOW, TrainingState.NORMAL),
    )

    assert decision.status is SafetyStatus.APPROVED
    assert decision.final_action is AdaptationAction.KEEP
    assert decision.confidence == 0.50
    assert _has_code(decision.warnings, "MISSING_READINESS_SCORE")
    assert _has_code(decision.warnings, "MISSING_SNAPSHOT")
    assert _has_code(decision.warnings, "MISSING_PLANNED_WORKOUT")


def test_safe_decision_is_approved_without_override() -> None:
    decision = validate_safety(
        _adaptation(AdaptationAction.REDUCE_VOLUME, confidence=0.75),
        _state(ReadinessState.GREEN, TrainingState.NORMAL, readiness_score=85),
        snapshot=_snapshot(pain_score=0),
        planned_workout=_workout(SessionType.LONG_RUN),
    )

    assert decision.status is SafetyStatus.APPROVED
    assert decision.final_action is AdaptationAction.REDUCE_VOLUME
    assert decision.confidence == 0.75
    assert _has_code(decision.reasons, "SAFETY_APPROVED")


def _adaptation(action: AdaptationAction, *, confidence: float = 0.75) -> AdaptationDecision:
    return AdaptationDecision(
        action=action,
        allowed_actions=tuple(AdaptationAction),
        confidence=confidence,
        thresholds_version="adaptation.v1",
        planned_workout_id="workout-1",
        reasons=(Evidence(code="TEST_ADAPTATION", message="Sanitized fixture."),),
    )


def _state(
    readiness: ReadinessState,
    training_state: TrainingState,
    *,
    readiness_score: float | None = None,
) -> AthleteStateAssessment:
    return AthleteStateAssessment(
        readiness=readiness,
        training_state=training_state,
        readiness_score=readiness_score,
        thresholds_version="athlete_state.v1",
        scores=(),
        evidence=(Evidence(code="TEST_STATE", message="Sanitized fixture."),),
    )


def _snapshot(pain_score: int | None) -> AthleteSnapshot:
    return AthleteSnapshot(
        snapshot_at=OBSERVED_AT,
        subjective_feedback=SubjectiveFeedback(
            recorded_at=OBSERVED_AT,
            pain_score=pain_score,
        ),
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


def _has_code(evidence: tuple[Evidence, ...], code: str) -> bool:
    return any(item.code == code for item in evidence)

