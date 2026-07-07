"""Models for the bounded LLM coach layer."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.engines import AdaptationAction, Evidence


class LLMCoachStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class LLMCoachPrompt(BaseModel):
    model_config = ConfigDict(frozen=True)

    system: str
    user: str
    allowed_actions: tuple[AdaptationAction, ...]
    locked_action: AdaptationAction


class LLMCoachDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposed_action: AdaptationAction
    summary: str
    rationale: str
    user_message: str
    uncertainty: tuple[str, ...] = ()
    abort_conditions: tuple[str, ...] = ()
    invented_targets: tuple[str, ...] = ()


class LLMCoachResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: LLMCoachStatus
    action: AdaptationAction
    summary: str
    rationale: str
    user_message: str
    evidence: tuple[Evidence, ...]
    uncertainty: tuple[str, ...] = ()
    abort_conditions: tuple[str, ...] = ()

