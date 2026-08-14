from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Base request for analysis"""
    url: Optional[HttpUrl] = Field(None, description="URL of the media file")


class AudioAnalysisRequest(AnalysisRequest):
    """Request model for audio analysis"""
    pass


class VideoAnalysisRequest(AnalysisRequest):
    """Request model for video analysis"""
    pass


class ArtifactDetection(BaseModel):
    """Detected artifacts in the media"""
    type: str = Field(..., description="Type of artifact detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    description: str = Field(..., description="Description of the artifact")


class AudioAnalysisDetails(BaseModel):
    """Detailed audio analysis results"""
    spectral_score: float = Field(..., ge=0.0, le=1.0, description="Spectral analysis score")
    pitch_consistency: float = Field(..., ge=0.0, le=1.0, description="Pitch consistency score")
    noise_detection: float = Field(..., ge=0.0, le=1.0, description="Artificial noise detection")
    artifacts: List[ArtifactDetection] = Field(default_factory=list)


class VideoAnalysisDetails(BaseModel):
    """Detailed video analysis results (for Programador 2)"""
    facial_consistency: Optional[float] = Field(None, ge=0.0, le=1.0)
    frame_artifacts: Optional[float] = Field(None, ge=0.0, le=1.0)
    compression_anomalies: Optional[float] = Field(None, ge=0.0, le=1.0)
    artifacts: List[ArtifactDetection] = Field(default_factory=list)


class MediaMetadata(BaseModel):
    """Metadata of the analyzed media"""
    duration: Optional[float] = Field(None, description="Duration in seconds")
    format: str = Field(..., description="File format")
    size: Optional[int] = Field(None, description="File size in bytes")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate (Hz)")
    channels: Optional[int] = Field(None, description="Number of audio channels")
    resolution: Optional[str] = Field(None, description="Video resolution (e.g., 1920x1080)")
    fps: Optional[float] = Field(None, description="Frames per second")


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    is_ai_generated: bool = Field(..., description="Whether the media is AI-generated")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    analysis_type: Literal["audio", "video", "both"] = Field(..., description="Type of analysis performed")
    audio_details: Optional[AudioAnalysisDetails] = None
    video_details: Optional[VideoAnalysisDetails] = None
    metadata: MediaMetadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time: float = Field(..., description="Processing time in seconds")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
