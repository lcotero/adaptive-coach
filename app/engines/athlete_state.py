"""Pure, deterministic assessment of athlete readiness and training state."""

from statistics import mean

from app.domain import AthleteSnapshot, SubjectiveFeeling
from app.engines.analysis_models import ActivityAnalysis, Evidence
from app.engines.state_models import (
    AthleteStateAssessment,
    AthleteStateContext,
    AthleteStateThresholds,
    ReadinessState,
    StateScore,
    TrainingState,
)

DEFAULT_STATE_THRESHOLDS = AthleteStateThresholds()


def assess_athlete_state(
    snapshot: AthleteSnapshot,
    recent_analyses: tuple[ActivityAnalysis, ...] = (),
    context: AthleteStateContext | None = None,
    thresholds: AthleteStateThresholds = DEFAULT_STATE_THRESHOLDS,
) -> AthleteStateAssessment:
    """Assess current readiness separately from longer-term training state."""
    context = context or AthleteStateContext()
    scores = (
        _recovery_score(snapshot, thresholds),
        _hrv_score(snapshot, thresholds),
        _sleep_score(snapshot, thresholds),
        _subjective_score(snapshot, thresholds),
        _execution_score(recent_analyses),
        _load_ratio_score(snapshot, thresholds),
    )
    readiness_score = _weighted_readiness(scores)
    readiness = _classify_readiness(readiness_score, snapshot, thresholds)
    training_state = _classify_training_state(
        snapshot=snapshot,
        recent_analyses=recent_analyses,
        context=context,
        readiness=readiness,
        thresholds=thresholds,
    )
    return AthleteStateAssessment(
        readiness=readiness,
        training_state=training_state,
        readiness_score=readiness_score,
        thresholds_version=thresholds.version,
        scores=scores,
        evidence=(
            Evidence(
                code="STATE_SEPARATION",
                message="Readiness is daily state; training_state is block response.",
            ),
            Evidence(
                code="NO_RECOMMENDATION",
                message="Sprint 4 classifies state only and does not generate adaptations.",
            ),
        ),
    )


def _weighted_readiness(scores: tuple[StateScore, ...]) -> float | None:
    values = [score.value for score in scores if score.value is not None]
    if not values:
        return None
    return mean(values)


def _classify_readiness(
    readiness_score: float | None,
    snapshot: AthleteSnapshot,
    thresholds: AthleteStateThresholds,
) -> ReadinessState:
    feedback = snapshot.subjective_feedback
    if feedback is not None and feedback.pain_score is not None:
        if feedback.pain_score >= thresholds.pain_red_min:
            return ReadinessState.RED
        if feedback.pain_score >= thresholds.pain_orange_min:
            return ReadinessState.ORANGE
    if readiness_score is None:
        return ReadinessState.YELLOW
    if readiness_score >= thresholds.green_min_score:
        return ReadinessState.GREEN
    if readiness_score >= thresholds.yellow_min_score:
        return ReadinessState.YELLOW
    if readiness_score >= thresholds.orange_min_score:
        return ReadinessState.ORANGE
    return ReadinessState.RED


def _classify_training_state(
    snapshot: AthleteSnapshot,
    recent_analyses: tuple[ActivityAnalysis, ...],
    context: AthleteStateContext,
    readiness: ReadinessState,
    thresholds: AthleteStateThresholds,
) -> TrainingState:
    if context.returning_from_break:
        return TrainingState.RETURNING
    if _is_race_ready(snapshot, context, readiness, thresholds):
        return TrainingState.RACE_READY
    if context.tapering:
        return TrainingState.TAPERING

    load_ratio = snapshot.training_load.load_ratio if snapshot.training_load is not None else None
    recovery_score = snapshot.recovery.recovery_score if snapshot.recovery is not None else None
    execution = _mean_execution_score(recent_analyses)
    feedback = snapshot.subjective_feedback

    if (
        load_ratio is not None
        and load_ratio >= thresholds.overreached_load_ratio_min
        and (
            recovery_score is not None
            and recovery_score < thresholds.recovery_orange_min
            or execution is not None
            and execution < thresholds.poor_execution_score_max
        )
    ):
        return TrainingState.OVERREACHED
    if (
        readiness is ReadinessState.RED
        or load_ratio is not None
        and load_ratio >= thresholds.fatigued_load_ratio_min
        or recovery_score is not None
        and recovery_score < thresholds.recovery_yellow_min
        or feedback is not None
        and feedback.feeling in {SubjectiveFeeling.VERY_TIRED, SubjectiveFeeling.POOR}
    ):
        return TrainingState.FATIGUED
    if (
        load_ratio is not None
        and load_ratio >= thresholds.accumulating_load_ratio_min
        or execution is not None
        and execution < thresholds.degraded_execution_score_max
        or readiness is ReadinessState.ORANGE
    ):
        return TrainingState.ACCUMULATING_FATIGUE
    if (
        recovery_score is not None
        and recovery_score >= thresholds.recovery_green_min
        and load_ratio is not None
        and load_ratio <= thresholds.low_load_ratio_max
    ):
        return TrainingState.RECOVERED
    return TrainingState.NORMAL


def _is_race_ready(
    snapshot: AthleteSnapshot,
    context: AthleteStateContext,
    readiness: ReadinessState,
    thresholds: AthleteStateThresholds,
) -> bool:
    if not context.tapering or context.race_within_days is None:
        return False
    if context.race_within_days > thresholds.race_ready_window_days:
        return False
    recovery_score = snapshot.recovery.recovery_score if snapshot.recovery is not None else None
    return (
        readiness in {ReadinessState.GREEN, ReadinessState.YELLOW}
        and recovery_score is not None
        and recovery_score >= thresholds.recovery_yellow_min
    )


def _recovery_score(
    snapshot: AthleteSnapshot, thresholds: AthleteStateThresholds
) -> StateScore:
    value = snapshot.recovery.recovery_score if snapshot.recovery is not None else None
    if value is None:
        return _missing_score("recovery", "Recovery score is unavailable.")
    if value >= thresholds.recovery_green_min:
        score = 100.0
    elif value >= thresholds.recovery_yellow_min:
        score = 75.0
    elif value >= thresholds.recovery_orange_min:
        score = 45.0
    else:
        score = 20.0
    return _score("recovery", score, "score_0_100", "RECOVERY_SCORE", f"Recovery score: {value}.")


def _hrv_score(snapshot: AthleteSnapshot, thresholds: AthleteStateThresholds) -> StateScore:
    if snapshot.recovery is None:
        return _missing_score("hrv", "Recovery metrics are unavailable.")
    hrv = snapshot.recovery.hrv_ms
    baseline = snapshot.recovery.hrv_baseline_ms
    if hrv is None or baseline is None:
        return _missing_score("hrv", "HRV or HRV baseline is unavailable.")
    ratio = hrv / baseline
    if ratio >= thresholds.hrv_green_min_ratio:
        score = 100.0
    elif ratio >= thresholds.hrv_yellow_min_ratio:
        score = 75.0
    elif ratio >= thresholds.hrv_orange_min_ratio:
        score = 45.0
    else:
        score = 20.0
    return _score("hrv", score, "score_0_100", "HRV_RATIO", f"HRV ratio: {ratio:.2f}.")


def _sleep_score(snapshot: AthleteSnapshot, thresholds: AthleteStateThresholds) -> StateScore:
    sleep = snapshot.recovery.sleep_duration_s if snapshot.recovery is not None else None
    if sleep is None:
        return _missing_score("sleep", "Sleep duration is unavailable.")
    hours = sleep / 3600
    if hours >= thresholds.sleep_green_min_hours:
        score = 100.0
    elif hours >= thresholds.sleep_yellow_min_hours:
        score = 75.0
    elif hours >= thresholds.sleep_orange_min_hours:
        score = 45.0
    else:
        score = 20.0
    return _score("sleep", score, "score_0_100", "SLEEP_DURATION", f"Sleep: {hours:.1f}h.")


def _subjective_score(
    snapshot: AthleteSnapshot, thresholds: AthleteStateThresholds
) -> StateScore:
    feedback = snapshot.subjective_feedback
    if feedback is None:
        return _missing_score("subjective", "Subjective feedback is unavailable.")
    if feedback.pain_score is not None and feedback.pain_score >= thresholds.pain_red_min:
        return _score("subjective", 0, "score_0_100", "PAIN_SIGNAL", "High pain score.")
    if feedback.pain_score is not None and feedback.pain_score >= thresholds.pain_orange_min:
        return _score("subjective", 30, "score_0_100", "PAIN_SIGNAL", "Moderate pain score.")
    if feedback.stress_level is not None and feedback.stress_level >= thresholds.stress_orange_min:
        return _score("subjective", 45, "score_0_100", "STRESS_SIGNAL", "High stress level.")
    if feedback.feeling in {SubjectiveFeeling.VERY_TIRED, SubjectiveFeeling.POOR}:
        return _score("subjective", 35, "score_0_100", "SUBJECTIVE_FATIGUE", "Poor feeling.")
    if feedback.feeling in {SubjectiveFeeling.VERY_GOOD, SubjectiveFeeling.GOOD}:
        return _score("subjective", 100, "score_0_100", "SUBJECTIVE_FEELING", "Good feeling.")
    return _score("subjective", 75, "score_0_100", "SUBJECTIVE_FEELING", "Neutral feeling.")


def _execution_score(recent_analyses: tuple[ActivityAnalysis, ...]) -> StateScore:
    score = _mean_execution_score(recent_analyses)
    if score is None:
        return _missing_score("recent_execution", "Recent execution scores are unavailable.")
    return _score(
        "recent_execution",
        score,
        "score_0_100",
        "RECENT_EXECUTION",
        "Mean recent execution score.",
    )


def _load_ratio_score(
    snapshot: AthleteSnapshot, thresholds: AthleteStateThresholds
) -> StateScore:
    ratio = snapshot.training_load.load_ratio if snapshot.training_load is not None else None
    if ratio is None:
        return _missing_score("load_ratio", "Load ratio is unavailable.")
    if ratio >= thresholds.overreached_load_ratio_min:
        score = 20.0
    elif ratio >= thresholds.fatigued_load_ratio_min:
        score = 35.0
    elif ratio >= thresholds.accumulating_load_ratio_min:
        score = 60.0
    elif ratio <= thresholds.low_load_ratio_max:
        score = 90.0
    else:
        score = 100.0
    return _score("load_ratio", score, "score_0_100", "LOAD_RATIO", f"Load ratio: {ratio}.")


def _mean_execution_score(recent_analyses: tuple[ActivityAnalysis, ...]) -> float | None:
    scores = [
        analysis.execution_score
        for analysis in recent_analyses
        if analysis.execution_score is not None
    ]
    if not scores:
        return None
    return mean(scores)


def _missing_score(name: str, message: str) -> StateScore:
    return StateScore(
        name=name,
        value=None,
        unit="score_0_100",
        evidence=(Evidence(code="MISSING_DATA", message=message),),
    )


def _score(name: str, value: float, unit: str, code: str, message: str) -> StateScore:
    return StateScore(
        name=name,
        value=value,
        unit=unit,
        evidence=(Evidence(code=code, message=message),),
    )
