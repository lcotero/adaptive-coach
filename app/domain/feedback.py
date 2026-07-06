"""Athlete-provided subjective observations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import SubjectiveFeeling


class SubjectiveFeedback(BaseModel):
    """Subjective feedback using explicit, documented scales."""

    model_config = ConfigDict(frozen=True)

    recorded_at: datetime
    rpe: int | None = Field(default=None, ge=1, le=10, description="RPE on a 1–10 scale")
    feeling: SubjectiveFeeling | None = None
    pain_score: int | None = Field(default=None, ge=0, le=10, description="Pain on a 0–10 scale")
    sleep_quality: int | None = Field(
        default=None, ge=1, le=5, description="Sleep quality on a 1–5 scale"
    )
    stress_level: int | None = Field(default=None, ge=1, le=5, description="Stress on a 1–5 scale")
    notes: str | None = None

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at(cls, value: datetime) -> datetime:
        """Require an unambiguous recording time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value
