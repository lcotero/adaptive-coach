"""Tests for bounded LLM coach behavior."""

from datetime import UTC, date, datetime

from app.coach import (
    LLMCoachDraft,
    LLMCoachPrompt,
    LLMCoachProvider,
    LLMCoachStatus,
    ShadowRecommendation,
    build_llm_coach_prompt,
    create_shadow_recommendation,
    generate_llm_coach_response,
    validate_llm_coach_draft,
)
from app.domain import (
    AthleteSnapshot,
    IntensityTargetType,
    PlannedWorkout,
    RecoveryState,
    SessionType,
    SubjectiveFeedback,
    TrainingLoadState,
)
from app.engines import AdaptationAction

OBSERVED_AT = datetime(2026, 7, 7, tzinfo=UTC)


class FakeProvider:
    def __init__(self, draft: LLMCoachDraft) -> None:
        self.draft = draft
        self.prompt: LLMCoachPrompt | None = None

    def generate(self, prompt: LLMCoachPrompt) -> LLMCoachDraft:
        self.prompt = prompt
        return self.draft


def test_prompt_locks_action_and_lists_allowed_actions() -> None:
    recommendation = _recommendation()

    prompt = build_llm_coach_prompt(recommendation)

    assert prompt.locked_action is recommendation.recommended_action
    assert recommendation.recommended_action in prompt.allowed_actions
    assert "Safety output is final" in prompt.system
    assert "Locked action" in prompt.user


def test_matching_draft_is_accepted() -> None:
    recommendation = _recommendation()
    draft = _draft(recommendation.recommended_action)

    response = validate_llm_coach_draft(recommendation, draft)

    assert response.status is LLMCoachStatus.ACCEPTED
    assert response.action is recommendation.recommended_action
    assert response.user_message == draft.user_message


def test_provider_generation_is_validated() -> None:
    recommendation = _recommendation()
    provider: LLMCoachProvider = FakeProvider(_draft(recommendation.recommended_action))

    response = generate_llm_coach_response(provider, recommendation)

    assert response.status is LLMCoachStatus.ACCEPTED


def test_draft_cannot_change_safety_validated_action() -> None:
    recommendation = _recommendation()
    unsafe_draft = _draft(AdaptationAction.KEEP)

    response = validate_llm_coach_draft(recommendation, unsafe_draft)

    assert response.status is LLMCoachStatus.REJECTED
    assert response.action is recommendation.recommended_action
    assert any(item.code == "SAFETY_ACTION_LOCKED" for item in response.evidence)
    assert any(item.code == "DETERMINISTIC_FALLBACK" for item in response.evidence)


def test_draft_cannot_invent_targets() -> None:
    recommendation = _recommendation()
    target_draft = _draft(
        recommendation.recommended_action,
        invented_targets=("Run 6x1000m at 4:10/km",),
    )

    response = validate_llm_coach_draft(recommendation, target_draft)

    assert response.status is LLMCoachStatus.REJECTED
    assert response.action is recommendation.recommended_action
    assert any(item.code == "INVENTED_TARGETS" for item in response.evidence)


def _recommendation() -> ShadowRecommendation:
    return create_shadow_recommendation(
        snapshot=AthleteSnapshot(
            snapshot_at=OBSERVED_AT,
            training_load=TrainingLoadState(load_ratio=1.2, observed_at=OBSERVED_AT),
            recovery=RecoveryState(
                recovery_score=72,
                hrv_ms=60,
                hrv_baseline_ms=60,
                sleep_duration_s=7 * 3600,
                observed_at=OBSERVED_AT,
            ),
            subjective_feedback=SubjectiveFeedback(recorded_at=OBSERVED_AT, pain_score=0),
        ),
        planned_workout=PlannedWorkout(
            id="workout-1",
            scheduled_date=date(2026, 7, 8),
            session_type=SessionType.THRESHOLD,
            title="Threshold",
            planned_duration_s=3600,
            intensity_target_type=IntensityTargetType.OPEN,
        ),
    )


def _draft(
    action: AdaptationAction,
    *,
    invented_targets: tuple[str, ...] = (),
) -> LLMCoachDraft:
    return LLMCoachDraft(
        proposed_action=action,
        summary="Conviene ajustar la sesión.",
        rationale="La recomendación respeta el estado y la validación de seguridad.",
        user_message="Hacé la versión ajustada y observá señales de aborto.",
        uncertainty=("Faltan algunos datos finos del contexto.",),
        abort_conditions=("Frenar si aparece dolor.",),
        invented_targets=invented_targets,
    )
