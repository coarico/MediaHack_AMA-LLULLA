from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal, Dict
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
    ml_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Machine learning deepfake score")
    edit_detection: Optional[float] = Field(None, ge=0.0, le=1.0, description="Manual edit/cut detection score")
    artifacts: List[ArtifactDetection] = Field(default_factory=list)


class VideoAnalysisDetails(BaseModel):
    """Detailed video analysis results (for Programador 2)"""
    facial_consistency: Optional[float] = Field(None, ge=0.0, le=1.0)
    frame_artifacts: Optional[float] = Field(None, ge=0.0, le=1.0)
    compression_anomalies: Optional[float] = Field(None, ge=0.0, le=1.0)
    artifacts: List[ArtifactDetection] = Field(default_factory=list)


class SegmentVerification(BaseModel):
    """Verification result for a single transcription segment"""
    segment_index: int = Field(..., description="Index of the segment")
    text: str = Field(..., description="Segment text")
    start: float = Field(0.0, description="Start time in seconds")
    end: float = Field(0.0, description="End time in seconds")
    label: str = Field("SIN_VERIFICAR", description="Verification label")
    source: str = Field("N/A", description="Verification source")
    fact_checks_found: int = Field(0, description="Number of fact-checks found")


class TranscriptionResult(BaseModel):
    """Speech-to-text transcription results"""
    text: str = Field(..., description="Transcribed text content")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    segments: Optional[List[dict]] = Field(None, description="Detailed transcription segments")
    segment_verifications: Optional[List[SegmentVerification]] = Field(None, description="Per-segment fact-check results")
    deepgram_backup: Optional[Dict] = Field(None, description="Transcripcion de respaldo/verificacion generada con Deepgram (independiente de la transcripcion principal)")


class FactCheckReview(BaseModel):
    """Individual fact-check review"""
    claim_text: str = Field(..., description="The claim being checked")
    claimant: Optional[str] = Field(None, description="Source of the claim")
    publisher: Optional[str] = Field(None, description="Fact-check publisher")
    url: Optional[str] = Field(None, description="URL to fact-check article")
    title: Optional[str] = Field(None, description="Title of fact-check")
    rating: Optional[str] = Field(None, description="Rating given by fact-checker")


class FactCheckResult(BaseModel):
    """Fact-checking results"""
    claim: Optional[str] = Field(None, description="Claim that was checked")
    fact_checks_found: int = Field(0, description="Number of fact-checks found")
    fact_checks: List[Dict] = Field(default_factory=list, description="Fact-check reviews (flexible)")
    status: Optional[str] = Field(None, description="API status")


class FakeNewsAnalysis(BaseModel):
    """Fake news content analysis results"""
    is_fake_news: bool = Field(..., description="Whether content is classified as fake news")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    label: Optional[str] = Field(None, description="Classification label")
    method: Optional[str] = Field(None, description="Method used (ml or heuristic)")
    details: Optional[str] = Field(None, description="Detailed analysis description")
    indicators_found: Optional[int] = Field(None, description="Number of fake news indicators")


class ContentAnalysisResult(BaseModel):
    """Complete content analysis including transcription, fake news and fact-checking"""
    has_transcription: bool = Field(False, description="Whether transcription was successful")
    transcription: Optional[TranscriptionResult] = None
    fake_news: Optional[FakeNewsAnalysis] = None
    fact_checking: Optional[FactCheckResult] = None
    extracted_claims: List[str] = Field(default_factory=list, description="Key claims extracted")
    web_context: Optional[Dict] = Field(None, description="Web search context and articles")
    llm_analysis: Optional[Dict] = Field(None, description="LLM analysis results (verdict, summary, etc.)")


class MediaMetadata(BaseModel):
    """Metadata of the analyzed media"""
    duration: Optional[float] = Field(None, description="Duration in seconds")
    format: str = Field(..., description="File format")
    size: Optional[int] = Field(None, description="File size in bytes")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate (Hz)")
    channels: Optional[int] = Field(None, description="Number of audio channels")
    resolution: Optional[str] = Field(None, description="Video resolution (e.g., 1920x1080)")
    fps: Optional[float] = Field(None, description="Frames per second")
    source_metadata: Optional[dict] = Field(None, description="Source metadata (YouTube, etc.)")


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    is_ai_generated: bool = Field(..., description="Whether the media is AI-generated")
    is_manipulated: Optional[bool] = Field(False, description="Whether the media is manipulated")
    is_misinformation: Optional[bool] = Field(False, description="Whether the content is misinformation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    analysis_type: Literal["audio", "video", "both"] = Field(..., description="Type of analysis performed")
    audio_details: Optional[AudioAnalysisDetails] = None
    video_details: Optional[VideoAnalysisDetails] = None
    content_analysis: Optional[ContentAnalysisResult] = None
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
