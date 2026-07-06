"""Tests for conservative completed-activity analysis."""

from datetime import UTC, datetime

from app.domain import Activity, ActivityLap, SessionType, SportType
from app.engines import ActivityAnalysisContext, MetricStatus, analyze_activity


def _activity(session: SessionType, paces: tuple[float, ...]) -> Activity:
    return Activity(
        id="sanitized",
        started_at=datetime(2026, 7, 1, tzinfo=UTC),
        sport_type=SportType.RUNNING,
        session_type=session,
        duration_s=sum(paces),
        laps=tuple(
            ActivityLap(
                index=index, duration_s=pace, avg_pace_s_per_km=pace, avg_hr_bpm=140 + index
            )
            for index, pace in enumerate(paces, 1)
        ),
    )


def test_stable_easy_run_produces_auditable_metrics() -> None:
    result = analyze_activity(
        _activity(SessionType.EASY, (360, 362, 361, 363)),
        context=ActivityAnalysisContext(steady_state_confirmed=True),
    )
    metrics = {metric.name: metric for metric in result.metrics}

    assert metrics["pace_stability"].status is MetricStatus.EVALUATED
    assert metrics["cardiac_drift"].status is MetricStatus.EVALUATED
    assert result.execution_score is not None
    assert result.evidence[0].code == "OBSERVATION_ONLY"


def test_interval_session_blocks_cardiac_drift() -> None:
    result = analyze_activity(
        _activity(SessionType.INTERVAL, (280, 400, 282, 405)),
        context=ActivityAnalysisContext(work_lap_indexes=(1, 3)),
    )
    drift = next(metric for metric in result.metrics if metric.name == "cardiac_drift")

    assert drift.status is MetricStatus.NOT_EVALUABLE
    assert "invalidates" in drift.evidence[0].message


def test_missing_laps_are_explicitly_not_evaluable() -> None:
    result = analyze_activity(_activity(SessionType.EASY, (360,)))

    assert all(metric.status is MetricStatus.NOT_EVALUABLE for metric in result.metrics)
    assert result.execution_score is None


def test_real_sanitized_strides_use_only_identified_work_laps() -> None:
    activity = _activity(
        SessionType.STRIDES,
        (
            396.78,
            256.82,
            379.52,
            268.83,
            369.48,
            258.61,
            564.23,
            344.96,
            331.20,
            272.29,
            388.05,
            263.02,
            384.72,
        ),
    )
    result = analyze_activity(
        activity,
        context=ActivityAnalysisContext(work_lap_indexes=(2, 4, 6, 8, 10, 12)),
    )
    metrics = {metric.name: metric for metric in result.metrics}

    assert metrics["interval_consistency"].status is MetricStatus.EVALUATED
    assert metrics["cardiac_drift"].status is MetricStatus.NOT_EVALUABLE
