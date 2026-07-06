"""Pure mappings from COROS boundary DTOs to domain models."""

from collections.abc import Mapping

from app.domain import (
    Activity,
    ActivityLap,
    IntensityTargetType,
    PlannedWorkout,
    RecoveryState,
    RunningFitnessState,
    SessionType,
    SportType,
    TrainingLoadState,
)
from app.integrations.coros.dto import (
    CorosActivityDTO,
    CorosFitnessDTO,
    CorosLapPayloadDTO,
    CorosRecoveryDTO,
    CorosTrainingLoadDTO,
    CorosWorkoutDTO,
)


class CorosMappingError(ValueError):
    """Raised when required provider semantics cannot be mapped safely."""


COROS_RUNNING_SPORT_CODES: Mapping[int, SportType] = {
    100: SportType.RUNNING,
    101: SportType.TREADMILL_RUNNING,
    102: SportType.TRAIL_RUNNING,
    103: SportType.TRACK_RUNNING,
}


def map_activity(dto: CorosActivityDTO, sport_codes: Mapping[int, SportType]) -> Activity:
    """Normalize an activity using an explicit, verified sport-code mapping."""
    sport_type = sport_codes.get(dto.sport_code)
    if sport_type is None:
        raise CorosMappingError(f"unmapped COROS sport code: {dto.sport_code}")
    return Activity(
        id=dto.label_id,
        started_at=dto.started_at,
        sport_type=sport_type,
        session_type=_enum_or_default(dto.session_label, SessionType, SessionType.UNKNOWN),
        title=dto.title,
        duration_s=dto.duration_s,
        distance_m=dto.distance_m,
        avg_pace_s_per_km=dto.avg_pace_s_per_km,
        avg_hr_bpm=dto.avg_hr_bpm,
        max_hr_bpm=dto.max_hr_bpm,
        avg_cadence_spm=dto.avg_cadence_spm,
        elevation_gain_m=dto.elevation_gain_m,
        elevation_loss_m=dto.elevation_loss_m,
        training_load=dto.training_load,
        aerobic_training_effect=dto.aerobic_training_effect,
        anaerobic_training_effect=dto.anaerobic_training_effect,
        perceived_effort=dto.perceived_effort,
        laps=tuple(ActivityLap(**lap.model_dump()) for lap in dto.laps),
    )


def map_training_load(dto: CorosTrainingLoadDTO) -> TrainingLoadState:
    return TrainingLoadState(**dto.model_dump())


def map_lap_payload(dto: CorosLapPayloadDTO) -> ActivityLap:
    """Convert verified COROS lap units into domain units."""
    return ActivityLap(
        index=dto.lap_index,
        distance_m=dto.distance_centimeters / 100,
        duration_s=dto.duration_s,
        avg_pace_s_per_km=dto.avg_pace_s_per_km,
        avg_hr_bpm=dto.avg_hr_bpm,
        max_hr_bpm=dto.max_hr_bpm,
        avg_cadence_spm=dto.avg_cadence_spm,
        avg_power_w=dto.avg_power_w,
        elevation_gain_m=dto.elevation_gain_m,
        elevation_loss_m=dto.elevation_loss_m,
    )


def map_recovery(dto: CorosRecoveryDTO) -> RecoveryState:
    return RecoveryState(**dto.model_dump())


def map_fitness(dto: CorosFitnessDTO) -> RunningFitnessState:
    return RunningFitnessState(**dto.model_dump())


def map_workout(dto: CorosWorkoutDTO) -> PlannedWorkout:
    """Normalize a planned workout while preserving unknown classifications."""
    return PlannedWorkout(
        id=dto.workout_id,
        scheduled_date=dto.scheduled_date,
        session_type=_enum_or_default(dto.session_label, SessionType, SessionType.UNKNOWN),
        title=dto.title,
        planned_duration_s=dto.planned_duration_s,
        planned_distance_m=dto.planned_distance_m,
        intensity_target_type=_enum_or_default(
            dto.intensity_label, IntensityTargetType, IntensityTargetType.OPEN
        ),
        target_min=dto.target_min,
        target_max=dto.target_max,
        notes=dto.notes,
    )


def _enum_or_default[T: str](value: str | None, enum_type: type[T], default: T) -> T:
    if value is None:
        return default
    try:
        return enum_type(value.upper())
    except ValueError:
        return default
