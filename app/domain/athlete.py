"""Aggregate athlete snapshots."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.activity import Activity
from app.domain.feedback import SubjectiveFeedback
from app.domain.fitness import RunningFitnessState
from app.domain.load import TrainingLoadState
from app.domain.recovery import RecoveryState
from app.domain.workout import PlannedWorkout


class AthleteSnapshot(BaseModel):
    """Athlete state observed at one point in time."""

    model_config = ConfigDict(frozen=True)

    snapshot_at: datetime
    recent_activities: tuple[Activity, ...] = ()
    training_load: TrainingLoadState | None = None
    recovery: RecoveryState | None = None
    running_fitness: RunningFitnessState | None = None
    subjective_feedback: SubjectiveFeedback | None = None
    planned_workout: PlannedWorkout | None = None

    @field_validator("snapshot_at")
    @classmethod
    def validate_snapshot_at(cls, value: datetime) -> datetime:
        """Require an unambiguous snapshot time."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value
