"""Read-only contract implemented by a future COROS transport."""

from datetime import date, datetime
from typing import Protocol

from app.integrations.coros.dto import (
    CorosActivityDTO,
    CorosFitnessDTO,
    CorosRecoveryDTO,
    CorosTrainingLoadDTO,
    CorosWorkoutDTO,
)


class CorosDataSource(Protocol):
    """Provider boundary; implementations may call MCP outside the domain."""

    def list_activities(self, start: datetime, end: datetime) -> tuple[CorosActivityDTO, ...]: ...

    def get_activity(self, label_id: str) -> CorosActivityDTO | None: ...

    def get_activity_fit(self, label_id: str) -> bytes | None: ...

    def get_training_load(self) -> CorosTrainingLoadDTO | None: ...

    def get_recovery(self) -> CorosRecoveryDTO | None: ...

    def get_fitness(self) -> CorosFitnessDTO | None: ...

    def list_workouts(self, start: date, end: date) -> tuple[CorosWorkoutDTO, ...]: ...
