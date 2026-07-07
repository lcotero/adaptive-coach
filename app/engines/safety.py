"""Final deterministic safety validation for adaptation decisions."""

from app.domain import AthleteSnapshot, PlannedWorkout, SessionType
from app.engines.adaptation_models import AdaptationAction, AdaptationDecision
from app.engines.analysis_models import Evidence
from app.engines.safety_models import (
    SafetyContext,
    SafetyDecision,
    SafetyStatus,
    SafetyThresholds,
)
from app.engines.state_models import AthleteStateAssessment, ReadinessState, TrainingState

DEFAULT_SAFETY_THRESHOLDS = SafetyThresholds()

_QUALITY_SESSION_TYPES = {
    SessionType.TEMPO,
    SessionType.THRESHOLD,
    SessionType.INTERVAL,
    SessionType.HILLS,
    SessionType.STRIDES,
    SessionType.RACE,
}
_ACTION_SEVERITY = {
    AdaptationAction.KEEP: 0,
    AdaptationAction.REDUCE_VOLUME: 1,
    AdaptationAction.REDUCE_REPETITIONS: 1,
    AdaptationAction.REDUCE_INTENSITY: 2,
    AdaptationAction.REPLACE_WITH_EASY: 3,
    AdaptationAction.RECOVERY_ONLY: 4,
    AdaptationAction.REST: 5,
}


def validate_safety(
    adaptation: AdaptationDecision,
    athlete_state: AthleteStateAssessment,
    snapshot: AthleteSnapshot | None = None,
    planned_workout: PlannedWorkout | None = None,
    context: SafetyContext | None = None,
    thresholds: SafetyThresholds = DEFAULT_SAFETY_THRESHOLDS,
) -> SafetyDecision:
    """Apply conservative safety overrides before any recommendation is surfaced."""
    context = context or SafetyContext()
    warnings = _warnings(adaptation, athlete_state, snapshot, planned_workout, context)

    if context.medical_warning_signals:
        return _decision(
            status=SafetyStatus.BLOCKED,
            original=adaptation.action,
            final=AdaptationAction.REST,
            confidence=thresholds.blocked_confidence,
            thresholds=thresholds,
            reasons=(
                Evidence(
                    code="MEDICAL_WARNING_SIGNAL",
                    message="Medical warning signals require blocking training recommendation.",
                ),
            ),
            warnings=warnings,
        )

    pain_score = _pain_score(snapshot)
    if pain_score is not None and pain_score >= thresholds.pain_block_min:
        return _decision(
            status=SafetyStatus.BLOCKED,
            original=adaptation.action,
            final=AdaptationAction.REST,
            confidence=thresholds.blocked_confidence,
            thresholds=thresholds,
            reasons=(
                Evidence(code="HIGH_PAIN_SIGNAL", message="High pain score blocks training."),
            ),
            warnings=warnings,
        )

    required_action = _required_safety_action(
        athlete_state=athlete_state,
        planned_workout=planned_workout,
        pain_score=pain_score,
        thresholds=thresholds,
    )
    if _is_more_conservative(required_action, adaptation.action):
        return _decision(
            status=SafetyStatus.MODIFIED,
            original=adaptation.action,
            final=required_action,
            confidence=min(adaptation.confidence, thresholds.modified_confidence_cap),
            thresholds=thresholds,
            reasons=(
                Evidence(
                    code="SAFETY_OVERRIDE",
                    message="Safety rule overrides the proposed adaptation action.",
                ),
            ),
            warnings=warnings,
        )

    if _has_insufficient_data(athlete_state, snapshot, planned_workout):
        return _decision(
            status=SafetyStatus.APPROVED,
            original=adaptation.action,
            final=adaptation.action,
            confidence=min(adaptation.confidence, thresholds.low_confidence_cap),
            thresholds=thresholds,
            reasons=(
                Evidence(
                    code="APPROVED_WITH_LOW_CONFIDENCE",
                    message="Decision is allowed, but confidence is capped by missing data.",
                ),
            ),
            warnings=warnings,
        )

    return _decision(
        status=SafetyStatus.APPROVED,
        original=adaptation.action,
        final=adaptation.action,
        confidence=adaptation.confidence,
        thresholds=thresholds,
        reasons=(Evidence(code="SAFETY_APPROVED", message="No safety override was required."),),
        warnings=warnings,
    )


def _required_safety_action(
    athlete_state: AthleteStateAssessment,
    planned_workout: PlannedWorkout | None,
    pain_score: int | None,
    thresholds: SafetyThresholds,
) -> AdaptationAction:
    if athlete_state.readiness is ReadinessState.RED:
        return AdaptationAction.REST
    if athlete_state.training_state is TrainingState.OVERREACHED:
        return AdaptationAction.RECOVERY_ONLY
    if pain_score is not None and pain_score >= thresholds.pain_modify_min:
        return AdaptationAction.RECOVERY_ONLY
    if _unsafe_quality_intensity(athlete_state, planned_workout):
        return AdaptationAction.REPLACE_WITH_EASY
    return AdaptationAction.KEEP


def _unsafe_quality_intensity(
    athlete_state: AthleteStateAssessment,
    planned_workout: PlannedWorkout | None,
) -> bool:
    if planned_workout is None or planned_workout.session_type not in _QUALITY_SESSION_TYPES:
        return False
    return (
        athlete_state.readiness is ReadinessState.ORANGE
        or athlete_state.training_state is TrainingState.FATIGUED
    )


def _is_more_conservative(required: AdaptationAction, proposed: AdaptationAction) -> bool:
    return _ACTION_SEVERITY[required] > _ACTION_SEVERITY[proposed]


def _has_insufficient_data(
    athlete_state: AthleteStateAssessment,
    snapshot: AthleteSnapshot | None,
    planned_workout: PlannedWorkout | None,
) -> bool:
    return (
        athlete_state.readiness_score is None
        or snapshot is None
        or planned_workout is None
    )


def _pain_score(snapshot: AthleteSnapshot | None) -> int | None:
    if snapshot is None or snapshot.subjective_feedback is None:
        return None
    return snapshot.subjective_feedback.pain_score


def _warnings(
    adaptation: AdaptationDecision,
    athlete_state: AthleteStateAssessment,
    snapshot: AthleteSnapshot | None,
    planned_workout: PlannedWorkout | None,
    context: SafetyContext,
) -> tuple[Evidence, ...]:
    warnings: list[Evidence] = []
    if athlete_state.readiness_score is None:
        warnings.append(
            Evidence(code="MISSING_READINESS_SCORE", message="Readiness score is unavailable.")
        )
    if snapshot is None:
        warnings.append(Evidence(code="MISSING_SNAPSHOT", message="Athlete snapshot is missing."))
    if planned_workout is None:
        warnings.append(
            Evidence(code="MISSING_PLANNED_WORKOUT", message="Planned workout is missing.")
        )
    if context.environment_warnings:
        warnings.append(
            Evidence(
                code="ENVIRONMENT_WARNING",
                message="Environmental warning signals were provided by the caller.",
            )
        )
    warnings.extend(adaptation.assumptions)
    return tuple(warnings)


def _decision(
    *,
    status: SafetyStatus,
    original: AdaptationAction,
    final: AdaptationAction,
    confidence: float,
    thresholds: SafetyThresholds,
    reasons: tuple[Evidence, ...],
    warnings: tuple[Evidence, ...],
) -> SafetyDecision:
    return SafetyDecision(
        status=status,
        original_action=original,
        final_action=final,
        confidence=confidence,
        thresholds_version=thresholds.version,
        reasons=reasons,
        warnings=warnings,
    )

