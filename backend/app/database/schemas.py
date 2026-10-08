from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator

UNCERTAIN_RECOMMENDATION = "Result should not be treated as definitive."


class DetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_hash: str
    prediction: str
    ai_probability: float
    real_probability: float
    confidence: str
    model_name: str
    processing_time_ms: int
    created_at: datetime
    member_scores: dict[str, float] | None = None
    forensics: dict | None = None
    recommendation: str | None = None
    cached: bool = False
    decided_by: str = "detectors"  # "provenance" when file metadata settled the answer
    model_ai_probability: float | None = None  # what the detectors alone estimated
    provenance: dict | None = None

    @field_validator("created_at")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        # SQLite drops tzinfo; timestamps are stored in UTC, so mark them as such for the browser.
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    @classmethod
    def from_row(cls, row, cached: bool = False) -> "DetectionOut":
        details = row.details or {}
        return cls(
            id=row.id, filename=row.filename, file_hash=row.file_hash, prediction=row.prediction,
            ai_probability=row.ai_probability, real_probability=row.real_probability, confidence=row.confidence,
            model_name=row.model_name, processing_time_ms=row.processing_time_ms, created_at=row.created_at,
            member_scores=details.get("member_scores"), forensics=details.get("forensics"),
            recommendation=UNCERTAIN_RECOMMENDATION if row.prediction == "UNCERTAIN" else None,
            cached=cached,
            decided_by=details.get("decided_by", "detectors"),
            model_ai_probability=details.get("model_ai_probability", row.ai_probability),
            provenance=details.get("provenance"),
        )


class DetectionPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DetectionOut]


class ModelVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_name: str
    version: str
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    created_at: datetime


class Statistics(BaseModel):
    total: int
    ai_generated: int
    real: int
    uncertain: int
    average_confidence: float | None  # mean of max(ai_probability, real_probability)
    average_processing_time_ms: float | None
    confidence_histogram: list[int]  # 10 bins of ai_probability, 0.0-0.1 ... 0.9-1.0
    processing_times_ms: list[int]  # most recent 200, for the latency chart
    latest_model: ModelVersionOut | None


class Health(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None
    device: str | None
    thresholds: dict[str, float] | None
    error: str | None = None
