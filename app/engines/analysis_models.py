"""Auditable output models for completed-activity analysis."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MetricStatus(StrEnum):
    EVALUATED = "EVALUATED"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    lap_indexes: tuple[int, ...] = ()


class AnalysisMetric(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    status: MetricStatus
    value: float | None = None
    unit: str | None = None
    evidence: tuple[Evidence, ...]


class ActivityAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    activity_id: str
    metrics: tuple[AnalysisMetric, ...]
    execution_score: float | None = Field(default=None, ge=0, le=100)
    evidence: tuple[Evidence, ...]


class ActivityAnalysisContext(BaseModel):
    """Caller-supplied workout structure; no structure is inferred from metrics."""

    model_config = ConfigDict(frozen=True)

    work_lap_indexes: tuple[int, ...] = ()
    steady_state_confirmed: bool = False
