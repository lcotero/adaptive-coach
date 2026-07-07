"""Auditable output models for deterministic safety validation."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.engines.adaptation_models import AdaptationAction
from app.engines.analysis_models import Evidence


class SafetyStatus(StrEnum):
    APPROVED = "APPROVED"
    MODIFIED = "MODIFIED"
    BLOCKED = "BLOCKED"


class SafetyContext(BaseModel):
    """Caller-supplied safety context; medical signals are never inferred silently."""

    model_config = ConfigDict(frozen=True)

    medical_warning_signals: tuple[str, ...] = ()
    environment_warnings: tuple[str, ...] = ()


class SafetyThresholds(BaseModel):
    """Versioned thresholds used by the deterministic safety engine."""

    model_config = ConfigDict(frozen=True)

    version: str = "safety.v1"
    pain_block_min: int = 7
    pain_modify_min: int = 4
    low_confidence_cap: float = 0.50
    modified_confidence_cap: float = 0.70
    blocked_confidence: float = 0.95


class SafetyDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: SafetyStatus
    original_action: AdaptationAction
    final_action: AdaptationAction
    confidence: float = Field(ge=0, le=1)
    thresholds_version: str
    reasons: tuple[Evidence, ...]
    warnings: tuple[Evidence, ...] = ()

