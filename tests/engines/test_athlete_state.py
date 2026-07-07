"""Tests for deterministic athlete-state assessment."""

from datetime import UTC, datetime

from app.domain import (
    AthleteSnapshot,
    RecoveryState,
    SubjectiveFeedback,
    SubjectiveFeeling,
    TrainingLoadState,
)
from app.engines import (
    ActivityAnalysis,
    AthleteStateContext,
    Evidence,
    ReadinessState,
    TrainingState,
    assess_athlete_state,
)

OBSERVED_AT = datetime(2026, 7, 7, tzinfo=UTC)


def test_assessment_separates_green_readiness_from_recovered_training_state() -> None:
    snapshot = _snapshot(recovery_score=86, hrv=64, hrv_baseline=62, sleep_hours=8, load_ratio=0.78)

    assessment = assess_athlete_state(snapshot)

    assert assessment.readiness is ReadinessState.GREEN
    assert assessment.training_state is TrainingState.RECOVERED
    assert assessment.thresholds_version == "athlete_state.v1"
    assert assessment.readiness_score is not None
    assert assessment.readiness_score >= 80


def test_missing_data_remains_explicit_without_fabricating_red_state() -> None:
    assessment = assess_athlete_state(AthleteSnapshot(snapshot_at=OBSERVED_AT))

    assert assessment.readiness is ReadinessState.YELLOW
    assert assessment.training_state is TrainingState.NORMAL
    assert assessment.readiness_score is None
    assert all(score.value is None for score in assessment.scores)


def test_pain_signal_overrides_daily_readiness_without_generating_recommendation() -> None:
    snapshot = _snapshot(
        recovery_score=90,
        hrv=70,
        hrv_baseline=68,
        sleep_hours=8,
        load_ratio=0.9,
        pain_score=8,
    )

    assessment = assess_athlete_state(snapshot)

    assert assessment.readiness is ReadinessState.RED
    assert assessment.training_state is TrainingState.FATIGUED
    assert any(evidence.code == "NO_RECOMMENDATION" for evidence in assessment.evidence)


def test_high_load_low_recovery_classifies_overreached() -> None:
    snapshot = _snapshot(recovery_score=30, hrv=45, hrv_baseline=60, sleep_hours=5, load_ratio=1.55)

    assessment = assess_athlete_state(snapshot)

    assert assessment.readiness is ReadinessState.RED
    assert assessment.training_state is TrainingState.OVERREACHED


def test_recent_execution_quality_contributes_to_accumulating_fatigue() -> None:
    snapshot = _snapshot(recovery_score=78, hrv=60, hrv_baseline=60, sleep_hours=7, load_ratio=1.0)
    analysis = ActivityAnalysis(
        activity_id="activity-1",
        metrics=(),
        execution_score=65,
        evidence=(Evidence(code="TEST", message="Sanitized fixture."),),
    )

    assessment = assess_athlete_state(snapshot, recent_analyses=(analysis,))

    assert assessment.training_state is TrainingState.ACCUMULATING_FATIGUE


def test_macrocycle_context_can_classify_returning_tapering_and_race_ready() -> None:
    snapshot = _snapshot(recovery_score=75, hrv=60, hrv_baseline=60, sleep_hours=7, load_ratio=0.75)

    returning = assess_athlete_state(
        snapshot,
        context=AthleteStateContext(returning_from_break=True, tapering=True, race_within_days=3),
    )
    tapering = assess_athlete_state(snapshot, context=AthleteStateContext(tapering=True))
    race_ready = assess_athlete_state(
        snapshot,
        context=AthleteStateContext(tapering=True, race_within_days=3),
    )

    assert returning.training_state is TrainingState.RETURNING
    assert tapering.training_state is TrainingState.TAPERING
    assert race_ready.training_state is TrainingState.RACE_READY


def _snapshot(
    *,
    recovery_score: float,
    hrv: float,
    hrv_baseline: float,
    sleep_hours: float,
    load_ratio: float,
    pain_score: int | None = None,
) -> AthleteSnapshot:
    return AthleteSnapshot(
        snapshot_at=OBSERVED_AT,
        training_load=TrainingLoadState(load_ratio=load_ratio, observed_at=OBSERVED_AT),
        recovery=RecoveryState(
            recovery_score=recovery_score,
            hrv_ms=hrv,
            hrv_baseline_ms=hrv_baseline,
            sleep_duration_s=sleep_hours * 3600,
            observed_at=OBSERVED_AT,
        ),
        subjective_feedback=SubjectiveFeedback(
            recorded_at=OBSERVED_AT,
            feeling=SubjectiveFeeling.NORMAL,
            pain_score=pain_score,
        ),
    )
