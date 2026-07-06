"""Pure, conservative analysis of completed activities."""

from math import fsum
from statistics import mean, pstdev

from app.domain import Activity, PlannedWorkout, SessionType
from app.engines.analysis_models import (
    ActivityAnalysis,
    ActivityAnalysisContext,
    AnalysisMetric,
    Evidence,
    MetricStatus,
)


def analyze_activity(
    activity: Activity,
    planned_workout: PlannedWorkout | None = None,
    context: ActivityAnalysisContext | None = None,
) -> ActivityAnalysis:
    """Analyze observable execution without inferring physiological causes."""
    context = context or ActivityAnalysisContext()
    pace = _pace_stability(activity)
    intervals = _interval_consistency(activity, context)
    decay = _pace_decay(activity)
    drift = _cardiac_drift(activity, context)
    comparison = _planned_comparison(activity, planned_workout)
    evaluated = [
        metric.value
        for metric in (pace, intervals, comparison)
        if metric.value is not None and metric.unit == "score_0_100"
    ]
    score = max(0.0, min(100.0, mean(evaluated))) if evaluated else None
    evidence = (
        Evidence(
            code="OBSERVATION_ONLY",
            message=(
                "Metrics describe execution and do not establish fatigue, heat, terrain, "
                "or medical causes."
            ),
        ),
    )
    return ActivityAnalysis(
        activity_id=activity.id,
        metrics=(pace, drift, intervals, decay, comparison),
        execution_score=score,
        evidence=evidence,
    )


def _pace_stability(activity: Activity) -> AnalysisMetric:
    values = [lap.avg_pace_s_per_km for lap in activity.laps if lap.avg_pace_s_per_km is not None]
    if len(values) < 2:
        return _missing("pace_stability", "At least two laps with pace are required.")
    coefficient = pstdev(values) / mean(values) * 100
    return _metric("pace_stability", max(0, 100 - coefficient * 5), "score_0_100", activity)


def _interval_consistency(activity: Activity, context: ActivityAnalysisContext) -> AnalysisMetric:
    if activity.session_type not in {SessionType.INTERVAL, SessionType.STRIDES, SessionType.HILLS}:
        return _missing("interval_consistency", "Session is not classified as interval-like.")
    if not context.work_lap_indexes:
        return _missing("interval_consistency", "Work laps were not identified explicitly.")
    work_indexes = set(context.work_lap_indexes)
    work_laps = [lap for lap in activity.laps if lap.index in work_indexes]
    values = [lap.avg_pace_s_per_km for lap in work_laps if lap.avg_pace_s_per_km is not None]
    if len(values) < 2:
        return _missing("interval_consistency", "At least two work laps with pace are required.")
    spread = (max(values) - min(values)) / mean(values) * 100
    return _metric("interval_consistency", max(0, 100 - spread * 4), "score_0_100", activity)


def _pace_decay(activity: Activity) -> AnalysisMetric:
    values = [lap.avg_pace_s_per_km for lap in activity.laps if lap.avg_pace_s_per_km is not None]
    if len(values) < 4:
        return _missing("pace_decay", "At least four laps with pace are required.")
    midpoint = len(values) // 2
    change = (mean(values[midpoint:]) / mean(values[:midpoint]) - 1) * 100
    return AnalysisMetric(
        name="pace_decay",
        status=MetricStatus.EVALUATED,
        value=change,
        unit="percent_slower_second_half",
        evidence=(Evidence(code="HALF_COMPARISON", message="Compared mean lap pace by halves."),),
    )


def _cardiac_drift(activity: Activity, context: ActivityAnalysisContext) -> AnalysisMetric:
    if activity.session_type in {SessionType.INTERVAL, SessionType.STRIDES, SessionType.HILLS}:
        return _missing("cardiac_drift", "Interval-like structure invalidates steady-state drift.")
    if not context.steady_state_confirmed:
        return _missing("cardiac_drift", "Steady-state structure was not confirmed.")
    pairs = [
        (lap.avg_hr_bpm, lap.avg_pace_s_per_km)
        for lap in activity.laps
        if lap.avg_hr_bpm is not None and lap.avg_pace_s_per_km is not None
    ]
    if len(pairs) < 4:
        return _missing(
            "cardiac_drift", "At least four laps with heart rate and pace are required."
        )
    midpoint = len(pairs) // 2
    first = fsum(hr / pace for hr, pace in pairs[:midpoint]) / midpoint
    second = fsum(hr / pace for hr, pace in pairs[midpoint:]) / (len(pairs) - midpoint)
    return AnalysisMetric(
        name="cardiac_drift",
        status=MetricStatus.EVALUATED,
        value=(second / first - 1) * 100,
        unit="percent_hr_pace_ratio_change",
        evidence=(
            Evidence(code="STEADY_STATE_ASSUMED", message="Compared HR-to-pace ratio by halves."),
        ),
    )


def _planned_comparison(activity: Activity, planned: PlannedWorkout | None) -> AnalysisMetric:
    if planned is None or planned.planned_duration_s is None:
        return _missing("planned_vs_actual", "Planned duration is unavailable.")
    difference = abs(activity.duration_s - planned.planned_duration_s) / max(
        planned.planned_duration_s, 1
    )
    return AnalysisMetric(
        name="planned_vs_actual",
        status=MetricStatus.EVALUATED,
        value=max(0, 100 - difference * 100),
        unit="score_0_100",
        evidence=(
            Evidence(code="DURATION_COMPARISON", message="Compared planned and actual duration."),
        ),
    )


def _missing(name: str, message: str) -> AnalysisMetric:
    return AnalysisMetric(
        name=name,
        status=MetricStatus.NOT_EVALUABLE,
        evidence=(Evidence(code="INSUFFICIENT_OR_INVALID_DATA", message=message),),
    )


def _metric(name: str, value: float, unit: str, activity: Activity) -> AnalysisMetric:
    return AnalysisMetric(
        name=name,
        status=MetricStatus.EVALUATED,
        value=value,
        unit=unit,
        evidence=(
            Evidence(
                code="LAP_VALUES",
                message="Calculated from normalized lap values.",
                lap_indexes=tuple(lap.index for lap in activity.laps),
            ),
        ),
    )
