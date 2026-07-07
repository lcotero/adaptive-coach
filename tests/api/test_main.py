"""Tests for the FastAPI application boundary."""

from datetime import UTC, date, datetime
from typing import Any

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)
OBSERVED_AT = datetime(2026, 7, 7, tzinfo=UTC)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_activity_analysis_endpoint() -> None:
    response = client.post(
        "/activity-analysis",
        json={
            "activity": _activity_payload(),
            "planned_workout": _workout_payload("EASY"),
            "context": {"steady_state_confirmed": True},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["activity_id"] == "activity-1"
    assert body["execution_score"] is not None
    assert any(metric["name"] == "cardiac_drift" for metric in body["metrics"])


def test_athlete_state_endpoint() -> None:
    response = client.post("/athlete-state", json={"snapshot": _snapshot_payload()})

    assert response.status_code == 200
    body = response.json()
    assert body["readiness"] in {"GREEN", "YELLOW", "ORANGE", "RED"}
    assert body["training_state"] in {
        "RECOVERED",
        "NORMAL",
        "ACCUMULATING_FATIGUE",
        "FATIGUED",
        "OVERREACHED",
        "RETURNING",
        "TAPERING",
        "RACE_READY",
    }


def test_shadow_recommendation_endpoint() -> None:
    response = client.post(
        "/shadow-recommendation",
        json={
            "snapshot": _snapshot_payload(recovery_score=72, load_ratio=1.2, pain_score=0),
            "planned_workout": _workout_payload("THRESHOLD"),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["planned_workout_id"] == "workout-1"
    assert body["recommended_action"] in {
        "KEEP",
        "REDUCE_VOLUME",
        "REDUCE_REPETITIONS",
        "REDUCE_INTENSITY",
        "REPLACE_WITH_EASY",
        "RECOVERY_ONLY",
        "REST",
    }
    assert body["safety"]["status"] in {"APPROVED", "MODIFIED", "BLOCKED"}


def test_llm_prompt_and_response_endpoints() -> None:
    recommendation = client.post(
        "/shadow-recommendation",
        json={
            "snapshot": _snapshot_payload(recovery_score=72, load_ratio=1.2, pain_score=0),
            "planned_workout": _workout_payload("THRESHOLD"),
        },
    ).json()

    prompt_response = client.post("/llm-coach-prompt", json={"recommendation": recommendation})
    assert prompt_response.status_code == 200
    prompt = prompt_response.json()
    assert prompt["locked_action"] == recommendation["recommended_action"]

    llm_response = client.post(
        "/llm-coach-response",
        json={
            "recommendation": recommendation,
            "draft": {
                "proposed_action": recommendation["recommended_action"],
                "summary": "Conviene respetar la recomendación.",
                "rationale": "La acción ya pasó por seguridad.",
                "user_message": "Seguí la recomendación y observá señales de aborto.",
            },
        },
    )

    assert llm_response.status_code == 200
    assert llm_response.json()["status"] == "ACCEPTED"


def _activity_payload() -> dict[str, Any]:
    return {
        "id": "activity-1",
        "started_at": OBSERVED_AT.isoformat(),
        "sport_type": "RUNNING",
        "session_type": "EASY",
        "duration_s": 2400,
        "distance_m": 8000,
        "laps": [
            {
                "index": 1,
                "distance_m": 1000,
                "duration_s": 300,
                "avg_pace_s_per_km": 300,
                "avg_hr_bpm": 140,
            },
            {
                "index": 2,
                "distance_m": 1000,
                "duration_s": 302,
                "avg_pace_s_per_km": 302,
                "avg_hr_bpm": 142,
            },
            {
                "index": 3,
                "distance_m": 1000,
                "duration_s": 304,
                "avg_pace_s_per_km": 304,
                "avg_hr_bpm": 145,
            },
            {
                "index": 4,
                "distance_m": 1000,
                "duration_s": 306,
                "avg_pace_s_per_km": 306,
                "avg_hr_bpm": 147,
            },
        ],
    }


def _snapshot_payload(
    recovery_score: float = 82,
    load_ratio: float = 0.95,
    pain_score: int = 0,
) -> dict[str, Any]:
    return {
        "snapshot_at": OBSERVED_AT.isoformat(),
        "training_load": {"load_ratio": load_ratio, "observed_at": OBSERVED_AT.isoformat()},
        "recovery": {
            "recovery_score": recovery_score,
            "hrv_ms": 60,
            "hrv_baseline_ms": 60,
            "sleep_duration_s": 7 * 3600,
            "observed_at": OBSERVED_AT.isoformat(),
        },
        "subjective_feedback": {
            "recorded_at": OBSERVED_AT.isoformat(),
            "pain_score": pain_score,
        },
    }


def _workout_payload(session_type: str) -> dict[str, Any]:
    return {
        "id": "workout-1",
        "scheduled_date": date(2026, 7, 8).isoformat(),
        "session_type": session_type,
        "title": "Planned workout",
        "planned_duration_s": 3600,
        "intensity_target_type": "OPEN",
    }
