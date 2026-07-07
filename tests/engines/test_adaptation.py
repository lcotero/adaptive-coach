"""Tests for deterministic adaptation selection."""

from datetime import date

from app.domain import IntensityTargetType, PlannedWorkout, SessionType
from app.engines import (
    ActivityAnalysis,
    AdaptationAction,
    AdaptationContext,
    AthleteStateAssessment,
    Evidence,
    ReadinessState,
    TrainingState,
    select_adaptation,
)


def test_missing_planned_workout_does_not_invent_a_session() -> None:
    decision = select_adaptation(_state(ReadinessState.GREEN, TrainingState.NORMAL))

    assert decision.action is AdaptationAction.KEEP
    assert decision.planned_workout_id is None
    assert _has_code(decision.reasons, "NO_PLANNED_WORKOUT")
    assert _has_code(decision.assumptions, "NO_NEW_TARGETS")


def test_red_readiness_selects_rest() -> None:
    decision = select_adaptation(
        _state(ReadinessState.RED, TrainingState.FATIGUED, readiness_score=35),
        planned_workout=_workout(SessionType.INTERVAL),
    )

    assert decision.action is AdaptationAction.REST
    assert decision.confidence == 0.90
    assert _has_code(decision.reasons, "RED_READINESS")


def test_overreached_state_selects_recovery_only_when_readiness_is_not_red() -> None:
    decision = select_adaptation(
        _state(ReadinessState.ORANGE, TrainingState.OVERREACHED, readiness_score=45),
        planned_workout=_workout(SessionType.EASY),
    )

    assert decision.action is AdaptationAction.RECOVERY_ONLY
    assert _has_code(decision.reasons, "OVERREACHED_STATE")


def test_fatigued_quality_session_is_replaced_with_easy() -> None:
    decision = select_adaptation(
        _state(ReadinessState.YELLOW, TrainingState.FATIGUED, readiness_score=62),
        planned_workout=_workout(SessionType.THRESHOLD),
    )

    assert decision.action is AdaptationAction.REPLACE_WITH_EASY


def test_accumulating_fatigue_reduces_intensity_for_quality_session() -> None:
    decision = select_adaptation(
        _state(ReadinessState.YELLOW, TrainingState.ACCUMULATING_FATIGUE, readiness_score=70),
        planned_workout=_workout(SessionType.TEMPO),
    )

    assert decision.action is AdaptationAction.REDUCE_INTENSITY
    assert decision.thresholds_version == "adaptation.v1"


def test_poor_recent_execution_reduces_repetitions_for_interval_workout() -> None:
    decision = select_adaptation(
        _state(ReadinessState.GREEN, TrainingState.NORMAL, readiness_score=85),
        planned_workout=_workout(SessionType.INTERVAL),
        recent_analyses=(
            _analysis(score=48),
        ),
    )

    assert decision.action is AdaptationAction.REDUCE_REPETITIONS
    assert _has_code(decision.reasons, "POOR_RECENT_EXECUTION")


def test_tapering_and_race_ready_preserve_phase_when_state_allows() -> None:
    tapering = select_adaptation(
        _state(ReadinessState.GREEN, TrainingState.TAPERING, readiness_score=85),
        planned_workout=_workout(SessionType.EASY),
        context=AdaptationContext(phase="taper", objective="10K"),
    )
    race_ready = select_adaptation(
        _state(ReadinessState.GREEN, TrainingState.RACE_READY, readiness_score=88),
        planned_workout=_workout(SessionType.RACE),
        context=AdaptationContext(phase="race_week", objective="10K", is_key_session=True),
    )

    assert tapering.action is AdaptationAction.KEEP
    assert race_ready.action is AdaptationAction.KEEP
    assert _has_code(tapering.assumptions, "OBJECTIVE_CONTEXT")
    assert _has_code(race_ready.assumptions, "KEY_SESSION_CONTEXT")


def test_missed_sessions_are_not_stacked_into_current_workout() -> None:
    decision = select_adaptation(
        _state(ReadinessState.GREEN, TrainingState.NORMAL, readiness_score=82),
        planned_workout=_workout(SessionType.LONG_RUN),
        context=AdaptationContext(missed_sessions=2),
    )

    assert decision.action is AdaptationAction.KEEP
    assert _has_code(decision.assumptions, "NO_MISSED_LOAD_STACKING")


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


def _has_code(evidence: tuple[Evidence, ...], code: str) -> bool:
    return any(item.code == code for item in evidence)
