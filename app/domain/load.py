"""Current training-load context."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrainingLoadState(BaseModel):
    """Observed load values without derived classifications."""

    model_config = ConfigDict(frozen=True)

    short_term_load: float | None = Field(default=None, ge=0)
    long_term_load: float | None = Field(default=None, ge=0)
    load_ratio: float | None = Field(default=None, ge=0)
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, value: datetime) -> datetime:
        """Require an unambiguous observation time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value
