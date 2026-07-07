"""Bounded LLM coach orchestration."""

from app.coach.llm_models import (
    LLMCoachDraft,
    LLMCoachPrompt,
    LLMCoachResponse,
    LLMCoachStatus,
)
from app.coach.llm_provider import LLMCoachProvider
from app.coach.shadow_models import ShadowRecommendation
from app.engines import AdaptationAction, Evidence, SafetyStatus


def build_llm_coach_prompt(recommendation: ShadowRecommendation) -> LLMCoachPrompt:
    """Build a constrained prompt from deterministic recommendation data."""
    system = (
        "You are a running coach explanation layer. Explain the deterministic recommendation. "
        "Do not invent pace targets, load limits, thresholds, diagnoses, or actions. "
        "Safety output is final."
    )
    user = "\n".join(
        [
            f"Locked action: {recommendation.recommended_action}",
            f"Confidence: {recommendation.confidence:.2f}",
            f"Readiness: {recommendation.athlete_state.readiness}",
            f"Training state: {recommendation.athlete_state.training_state}",
            f"Safety status: {recommendation.safety.status}",
            "Evidence:",
            *[f"- {item.code}: {item.message}" for item in recommendation.evidence],
            "Uncertainty:",
            *[f"- {item.code}: {item.message}" for item in recommendation.uncertainty],
            "Abort conditions:",
            *[f"- {item.code}: {item.message}" for item in recommendation.abort_conditions],
        ]
    )
    return LLMCoachPrompt(
        system=system,
        user=user,
        allowed_actions=recommendation.adaptation.allowed_actions,
        locked_action=recommendation.recommended_action,
    )


def generate_llm_coach_response(
    provider: LLMCoachProvider,
    recommendation: ShadowRecommendation,
) -> LLMCoachResponse:
    """Generate and validate a natural-language coaching response."""
    prompt = build_llm_coach_prompt(recommendation)
    draft = provider.generate(prompt)
    return validate_llm_coach_draft(recommendation, draft)


def validate_llm_coach_draft(
    recommendation: ShadowRecommendation,
    draft: LLMCoachDraft,
) -> LLMCoachResponse:
    """Accept only drafts that stay inside deterministic boundaries."""
    rejection_reasons = _rejection_reasons(recommendation, draft)
    if rejection_reasons:
        return _fallback_response(recommendation, rejection_reasons)
    return LLMCoachResponse(
        status=LLMCoachStatus.ACCEPTED,
        action=recommendation.recommended_action,
        summary=draft.summary,
        rationale=draft.rationale,
        user_message=draft.user_message,
        uncertainty=draft.uncertainty,
        abort_conditions=draft.abort_conditions,
        evidence=(
            Evidence(
                code="LLM_WITHIN_BOUNDARIES",
                message="LLM draft matched the locked action and did not invent targets.",
            ),
        ),
    )


def _rejection_reasons(
    recommendation: ShadowRecommendation,
    draft: LLMCoachDraft,
) -> tuple[Evidence, ...]:
    reasons: list[Evidence] = []
    if draft.proposed_action not in recommendation.adaptation.allowed_actions:
        reasons.append(
            Evidence(
                code="ACTION_NOT_ALLOWED",
                message="LLM proposed an action outside the allowed action set.",
            )
        )
    if draft.proposed_action is not recommendation.recommended_action:
        reasons.append(
            Evidence(
                code="SAFETY_ACTION_LOCKED",
                message="LLM attempted to change the safety-validated action.",
            )
        )
    if draft.invented_targets:
        reasons.append(
            Evidence(
                code="INVENTED_TARGETS",
                message="LLM draft included pace, load or threshold targets not supplied.",
            )
        )
    return tuple(reasons)


def _fallback_response(
    recommendation: ShadowRecommendation,
    reasons: tuple[Evidence, ...],
) -> LLMCoachResponse:
    status = recommendation.safety.status
    if status is SafetyStatus.BLOCKED:
        summary = "La recomendación queda bloqueada por seguridad."
    elif status is SafetyStatus.MODIFIED:
        summary = "La recomendación fue ajustada por seguridad."
    else:
        summary = "La recomendación determinística se mantiene."
    return LLMCoachResponse(
        status=LLMCoachStatus.REJECTED,
        action=recommendation.recommended_action,
        summary=summary,
        rationale="Se usa una respuesta segura porque el borrador del LLM salió de los límites.",
        user_message=_fallback_message(recommendation.recommended_action),
        evidence=(
            *reasons,
            Evidence(
                code="DETERMINISTIC_FALLBACK",
                message="Returned deterministic fallback instead of unsafe LLM draft.",
            ),
        ),
        uncertainty=tuple(item.message for item in recommendation.uncertainty),
        abort_conditions=tuple(item.message for item in recommendation.abort_conditions),
    )


def _fallback_message(action: AdaptationAction) -> str:
    return (
        f"Acción recomendada: {action}. "
        "La explicación se limita a la salida validada por los motores determinísticos."
    )

