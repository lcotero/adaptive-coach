"""Provider-independent planned workouts."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import IntensityTargetType, SessionType


class PlannedWorkout(BaseModel):
    """A minimal planned session representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    scheduled_date: date
    session_type: SessionType
    title: str = Field(min_length=1)
    planned_duration_s: float | None = Field(default=None, ge=0)
    planned_distance_m: float | None = Field(default=None, ge=0)
    intensity_target_type: IntensityTargetType
    target_min: float | None = None
    target_max: float | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_target_range(self) -> "PlannedWorkout":
        """Ensure a complete target range is ordered."""
        if (
            self.target_min is not None
            and self.target_max is not None
            and self.target_min > self.target_max
        ):
            raise ValueError("target_min must be less than or equal to target_max")
        return self
