"""Schemas Pydantic especificos del analisis de video.

Se mantienen separados de app/models/schemas.py (compartido, propiedad del
Programador 1) para no pisar su trabajo. Cuando ese archivo exista, estos
modelos se pueden fusionar ahi.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class VideoAnalysisMetadata(BaseModel):
    duration: float
    format: str
    fps: float
    frames_analyzed: int
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VideoAnalysisDetail(BaseModel):
    video_score: float
    ml_score: float
    heuristic_score: float
    artifacts_detected: list[str]


class VideoAnalysisResponse(BaseModel):
    is_ai_generated: bool
    confidence: float
    analysis: VideoAnalysisDetail
    metadata: VideoAnalysisMetadata


class VideoJobAcceptedResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.QUEUED


class VideoJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    result: Optional[VideoAnalysisResponse] = None
    error: Optional[str] = None
