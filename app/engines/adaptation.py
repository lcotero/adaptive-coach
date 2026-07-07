"""Pure, conservative selection of allowed workout adaptation actions."""

from statistics import mean

from app.domain import PlannedWorkout, SessionType
from app.engines.adaptation_models import (
    AdaptationAction,
    AdaptationContext,
    AdaptationDecision,
    AdaptationThresholds,
)
from app.engines.analysis_models import ActivityAnalysis, Evidence
from app.engines.state_models import AthleteStateAssessment, ReadinessState, TrainingState

DEFAULT_ADAPTATION_THRESHOLDS = AdaptationThresholds()

_ALL_ACTIONS = tuple(AdaptationAction)
_QUALITY_SESSION_TYPES = {
    SessionType.TEMPO,
    SessionType.THRESHOLD,
    SessionType.INTERVAL,
    SessionType.HILLS,
    SessionType.STRIDES,
    SessionType.RACE,
}
_VOLUME_SESSION_TYPES = {SessionType.EASY, SessionType.LONG_RUN, SessionType.RECOVERY}


def select_adaptation(
    athlete_state: AthleteStateAssessment,
    planned_workout: PlannedWorkout | None = None,
    recent_analyses: tuple[ActivityAnalysis, ...] = (),
    context: AdaptationContext | None = None,
    thresholds: AdaptationThresholds = DEFAULT_ADAPTATION_THRESHOLDS,
) -> AdaptationDecision:
    """Select one allowed action without inventing load, targets or future compensation."""
    context = context or AdaptationContext()
    assumptions = _assumptions(planned_workout, context)
    recent_execution = _mean_execution_score(recent_analyses)

    if planned_workout is None:
        action = AdaptationAction.KEEP
        reasons = (
            Evidence(
                code="NO_PLANNED_WORKOUT",
                message="No workout is available to adapt; no new session is invented.",
            ),
        )
    elif athlete_state.readiness is ReadinessState.RED:
        action = AdaptationAction.REST
        reasons = (Evidence(code="RED_READINESS", message="Daily readiness is RED."),)
    elif athlete_state.training_state is TrainingState.OVERREACHED:
        action = AdaptationAction.RECOVERY_ONLY
        reasons = (
            Evidence(code="OVERREACHED_STATE", message="Training state is OVERREACHED."),
        )
    elif athlete_state.training_state is TrainingState.FATIGUED:
        action = _fatigued_action(planned_workout)
        reasons = (Evidence(code="FATIGUED_STATE", message="Training state is FATIGUED."),)
    elif athlete_state.readiness is ReadinessState.ORANGE:
        action = _orange_readiness_action(planned_workout)
        reasons = (Evidence(code="ORANGE_READINESS", message="Daily readiness is ORANGE."),)
    elif athlete_state.training_state is TrainingState.RETURNING:
        action = AdaptationAction.REDUCE_VOLUME
        reasons = (
            Evidence(
                code="RETURNING_STATE",
                message="Return-to-training context favors reduced volume.",
            ),
        )
    elif athlete_state.training_state in {TrainingState.TAPERING, TrainingState.RACE_READY}:
        action = AdaptationAction.KEEP
        reasons = (
            Evidence(
                code="PHASE_PRESERVED",
                message="Taper/race context is preserved unless stronger state signals override.",
            ),
        )
    elif recent_execution is not None and recent_execution < thresholds.poor_execution_score_max:
        action = _poor_execution_action(planned_workout)
        reasons = (
            Evidence(
                code="POOR_RECENT_EXECUTION",
                message="Recent execution score is below the poor-execution threshold.",
            ),
        )
    elif (
        athlete_state.training_state is TrainingState.ACCUMULATING_FATIGUE
        or recent_execution is not None
        and recent_execution < thresholds.degraded_execution_score_max
    ):
        action = _accumulating_fatigue_action(planned_workout)
        reasons = (
            Evidence(
                code="ACCUMULATING_FATIGUE",
                message="Current state favors a conservative reduction.",
            ),
        )
    else:
        action = AdaptationAction.KEEP
        reasons = (
            Evidence(
                code="STATE_SUPPORTS_PLAN",
                message="No deterministic rule requires changing the planned workout.",
            ),
        )

    return AdaptationDecision(
        action=action,
        allowed_actions=_ALL_ACTIONS,
        confidence=_confidence(athlete_state, action, thresholds),
        thresholds_version=thresholds.version,
        planned_workout_id=planned_workout.id if planned_workout is not None else None,
        reasons=reasons,
        assumptions=assumptions,
    )


def _fatigued_action(planned_workout: PlannedWorkout) -> AdaptationAction:
    if planned_workout.session_type in _QUALITY_SESSION_TYPES:
        return AdaptationAction.REPLACE_WITH_EASY
    return AdaptationAction.RECOVERY_ONLY


def _orange_readiness_action(planned_workout: PlannedWorkout) -> AdaptationAction:
    if planned_workout.session_type in _QUALITY_SESSION_TYPES:
        return AdaptationAction.REDUCE_INTENSITY
    if planned_workout.session_type in _VOLUME_SESSION_TYPES:
        return AdaptationAction.REDUCE_VOLUME
    return AdaptationAction.REPLACE_WITH_EASY


def _poor_execution_action(planned_workout: PlannedWorkout) -> AdaptationAction:
    if planned_workout.session_type in _QUALITY_SESSION_TYPES:
        return AdaptationAction.REDUCE_REPETITIONS
    return AdaptationAction.REDUCE_VOLUME


def _accumulating_fatigue_action(planned_workout: PlannedWorkout) -> AdaptationAction:
    if planned_workout.session_type in _QUALITY_SESSION_TYPES:
        return AdaptationAction.REDUCE_INTENSITY
    return AdaptationAction.REDUCE_VOLUME


def _confidence(
    athlete_state: AthleteStateAssessment,
    action: AdaptationAction,
    thresholds: AdaptationThresholds,
) -> float:
    if athlete_state.readiness_score is None:
        return thresholds.low_confidence_missing_readiness_score
    if action in {AdaptationAction.REST, AdaptationAction.RECOVERY_ONLY}:
        return thresholds.high_confidence
    return thresholds.normal_confidence


def _mean_execution_score(recent_analyses: tuple[ActivityAnalysis, ...]) -> float | None:
    values = [
        analysis.execution_score
        for analysis in recent_analyses
        if analysis.execution_score is not None
    ]
    if not values:
        return None
    return mean(values)


def _assumptions(
    planned_workout: PlannedWorkout | None,
    context: AdaptationContext,
) -> tuple[Evidence, ...]:
    assumptions: list[Evidence] = [
        Evidence(
            code="NO_COROS_WRITE_BACK",
            message="The decision is read-only and does not modify COROS.",
        ),
        Evidence(
            code="NO_NEW_TARGETS",
            message=(
                "The engine selects an allowed action but does not invent pace or load targets."
            ),
        ),
    ]
    if planned_workout is not None and context.is_key_session:
        assumptions.append(
            Evidence(
                code="KEY_SESSION_CONTEXT",
                message="The planned session was marked as key and is preserved when state allows.",
            )
        )
    if context.missed_sessions > 0:
        assumptions.append(
            Evidence(
                code="NO_MISSED_LOAD_STACKING",
                message="Missed sessions are not compensated by adding load to this workout.",
            )
        )
    if context.phase is not None or context.objective is not None:
        assumptions.append(
            Evidence(
                code="OBJECTIVE_CONTEXT",
                message="Phase and objective context are carried as evidence, not free-form rules.",
            )
        )
    return tuple(assumptions)
