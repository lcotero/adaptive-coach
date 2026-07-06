"""Read-only COROS integration boundary."""

from app.integrations.coros.contracts import CorosDataSource
from app.integrations.coros.dto import (
    CorosActivityDTO,
    CorosActivityLapDTO,
    CorosFitnessDTO,
    CorosLapPayloadDTO,
    CorosRecoveryDTO,
    CorosTrainingLoadDTO,
    CorosWorkoutDTO,
)
from app.integrations.coros.mappers import (
    CorosMappingError,
    map_activity,
    map_fitness,
    map_lap_payload,
    map_recovery,
    map_training_load,
    map_workout,
)

__all__ = [
    "CorosActivityDTO",
    "CorosActivityLapDTO",
    "CorosDataSource",
    "CorosFitnessDTO",
    "CorosLapPayloadDTO",
    "CorosMappingError",
    "CorosRecoveryDTO",
    "CorosTrainingLoadDTO",
    "CorosWorkoutDTO",
    "map_activity",
    "map_fitness",
    "map_lap_payload",
    "map_recovery",
    "map_training_load",
    "map_workout",
]
