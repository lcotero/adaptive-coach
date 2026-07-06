"""Strongly typed values used by the internal domain."""

from enum import StrEnum


class SportType(StrEnum):
    """Provider-independent sport classification."""

    RUNNING = "RUNNING"
    TRAIL_RUNNING = "TRAIL_RUNNING"
    TRACK_RUNNING = "TRACK_RUNNING"
    TREADMILL_RUNNING = "TREADMILL_RUNNING"
    STRENGTH = "STRENGTH"
    WALKING = "WALKING"
    CYCLING = "CYCLING"
    SWIMMING = "SWIMMING"
    OTHER = "OTHER"


class SessionType(StrEnum):
    """Training-session purpose."""

    EASY = "EASY"
    RECOVERY = "RECOVERY"
    LONG_RUN = "LONG_RUN"
    TEMPO = "TEMPO"
    THRESHOLD = "THRESHOLD"
    INTERVAL = "INTERVAL"
    HILLS = "HILLS"
    STRIDES = "STRIDES"
    RACE = "RACE"
    STRENGTH = "STRENGTH"
    CROSS_TRAINING = "CROSS_TRAINING"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class IntensityTargetType(StrEnum):
    """Metric used to express a planned intensity target."""

    PACE = "PACE"
    HEART_RATE = "HEART_RATE"
    POWER = "POWER"
    RPE = "RPE"
    OPEN = "OPEN"


class SubjectiveFeeling(StrEnum):
    """Athlete's overall subjective feeling."""

    VERY_GOOD = "VERY_GOOD"
    GOOD = "GOOD"
    NORMAL = "NORMAL"
    TIRED = "TIRED"
    VERY_TIRED = "VERY_TIRED"
    POOR = "POOR"
