from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from datetime import datetime

from app.config import settings
from app.models import (
    HealthResponse,
    AnalysisResponse,
    AudioAnalysisRequest,
    VideoAnalysisRequest,
    ErrorResponse
)
from app.services.audio_analyzer import AudioAnalyzer
from app.services.video_analyzer import VideoAnalyzer
from app.services.transcription_service import TranscriptionService
from app.services.content_analyzer import ContentAnalyzer
from app.services.fact_checker import FactChecker
from app.utils.file_handler import FileHandler

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio para detección de contenido de audio/video generado por IA",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
audio_analyzer = AudioAnalyzer()
video_analyzer = VideoAnalyzer()
transcription_service = TranscriptionService()
content_analyzer = ContentAnalyzer()
fact_checker = FactChecker()
file_handler = FileHandler()


async def perform_content_analysis(file_path: str, is_video: bool = False) -> dict:
    """
    Perform complete content analysis: transcription, fake news, fact-checking
    Each transcription segment is fact-checked individually.
    
    Args:
        file_path: Path to media file
        is_video: Whether the file is a video
        
    Returns:
        dict: Content analysis results
    """
    try:
        # Transcription
        if is_video:
            transcription = await transcription_service.transcribe_video(file_path)
        else:
            transcription = await transcription_service.transcribe(file_path)
        
        text = transcription.get('text', '')
        
        if not text:
            return {
                'has_transcription': False,
                'transcription': None,
                'fake_news': None,
                'fact_checking': None,
                'extracted_claims': []
            }
        
        # Content analysis
        fake_news = await content_analyzer.analyze_content(text)
        
        # Extract claims
        extracted_claims = await content_analyzer.extract_claims(text)
        
        # Fact-checking (full text)
        fact_checking = await fact_checker.analyze_text(text)
        
        # Per-segment fact-checking
        segments = transcription.get('segments', [])
        segment_verifications = []
        
        if segments:
            print(f"🔍 Fact-checking {min(len(segments), 6)} segments...")
            for idx, segment in enumerate(segments[:6]):
                seg_text = segment.get('text', '').strip()
                if len(seg_text) < 10:
                    continue
                
                # Check this segment with Google Fact Check
                seg_result = await fact_checker.check_claim(seg_text)
                
                checks_found = seg_result.get('fact_checks_found', 0)
                fact_checks = seg_result.get('fact_checks', [])
                
                if checks_found > 0 and fact_checks:
                    first_check = fact_checks[0]
                    rating = first_check.get('rating', '').lower()
                    publisher = first_check.get('publisher', 'N/A')
                    
                    # Determine label from rating
                    if any(w in rating for w in ['false', 'falso', 'incorrecto', 'mentira', 'fake']):
                        label = 'FALSO'
                    elif any(w in rating for w in ['misleading', 'engañoso', 'impreciso', 'mixed']):
                        label = 'IMPRECISO'
                    elif any(w in rating for w in ['true', 'verdadero', 'correcto', 'accurate']):
                        label = 'VERIFICADO'
                    else:
                        label = 'DISPUTADO'
                    
                    source = publisher
                else:
                    label = 'SIN_VERIFICAR'
                    source = 'N/A'
                
                segment_verifications.append({
                    'segment_index': idx,
                    'text': seg_text,
                    'start': segment.get('start', 0.0),
                    'end': segment.get('end', 0.0),
                    'label': label,
                    'source': source,
                    'fact_checks_found': checks_found
                })
            
            print(f"✅ Segment verification complete: {len(segment_verifications)} segments checked")
        
        transcription['segment_verifications'] = segment_verifications
        
        return {
            'has_transcription': True,
            'transcription': transcription,
            'fake_news': fake_news,
            'fact_checking': fact_checking,
            'extracted_claims': extracted_claims
        }
        
    except Exception as e:
        print(f"⚠️ Content analysis failed: {e}")
        return {
            'has_transcription': False,
            'transcription': None,
            'fake_news': None,
            'fact_checking': None,
            'extracted_claims': []
        }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    import traceback
    print(f"❌ UNHANDLED ERROR: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.debug else None
        ).model_dump()
    )


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the current status of the service
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )


@app.post("/api/v1/analyze/audio", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_audio_file(
    file: UploadFile = File(..., description="Audio file to analyze")
):
    """
    Analyze an audio file for AI-generated content detection
    
    - **file**: Audio file (mp3, wav, ogg, m4a, flac)
    
    Returns analysis results with confidence score
    """
    start_time = time.time()
    
    try:
        # Validate file
        file_handler.validate_audio_file(file)
        
        # Save temporary file
        temp_path = await file_handler.save_temp_file(file)
        
        try:
            # Analyze audio
            result = await audio_analyzer.analyze(temp_path)
            
            # Perform content analysis
            content_analysis_dict = await perform_content_analysis(temp_path)
            from app.models.schemas import ContentAnalysisResult
            result.content_analysis = ContentAnalysisResult(**content_analysis_dict)
            
            # Update manipulation and misinformation flags
            if content_analysis_dict.get('fake_news'):
                result.is_misinformation = content_analysis_dict['fake_news'].get('is_fake_news', False)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            return result
            
        finally:
            # Clean up temporary file
            file_handler.cleanup_file(temp_path)
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}"
        )


@app.post("/api/v1/analyze/video", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_video_file(
    file: UploadFile = File(..., description="Video file to analyze")
):
    """
    Analyze a video file for AI-generated content detection (deepfake)

    - **file**: Video file (mp4, avi, mov, mkv, webm)

    Returns analysis results with confidence score
    """
    start_time = time.time()

    try:
        # Validate file
        file_handler.validate_video_file(file)

        # Save temporary file
        temp_path = await file_handler.save_temp_file(file)

        try:
            # Analyze video
            result = await video_analyzer.analyze(temp_path)

            # Perform content analysis (extract audio + transcribe)
            content_analysis_dict = await perform_content_analysis(temp_path, is_video=True)
            from app.models.schemas import ContentAnalysisResult
            result.content_analysis = ContentAnalysisResult(**content_analysis_dict)

            # Update manipulation and misinformation flags
            if content_analysis_dict.get('fake_news'):
                result.is_misinformation = content_analysis_dict['fake_news'].get('is_fake_news', False)

            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time

            return result

        finally:
            # Clean up temporary file
            file_handler.cleanup_file(temp_path)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing video: {str(e)}"
        )


@app.post("/api/v1/analyze/url", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_from_url(request: AudioAnalysisRequest):
    """
    Analyze audio/video from URL
    
    - **url**: URL of the media file
    
    Returns analysis results with confidence score
    """
    start_time = time.time()
    
    try:
        if not request.url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL is required"
            )
        
        # Download file from URL
        temp_path, source_metadata = await file_handler.download_from_url(str(request.url))
        
        try:
            # Determine file type and analyze
            is_video = file_handler.is_video_file(temp_path)
            
            if file_handler.is_audio_file(temp_path):
                result = await audio_analyzer.analyze(temp_path)
            elif is_video:
                result = await video_analyzer.analyze(temp_path)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file type. Please provide an audio or video file."
                )
            
            # Add source metadata if available (YouTube)
            if source_metadata:
                result.metadata.source_metadata = source_metadata
            
            # Perform content analysis
            content_analysis_dict = await perform_content_analysis(temp_path, is_video=is_video)
            from app.models.schemas import ContentAnalysisResult
            result.content_analysis = ContentAnalysisResult(**content_analysis_dict)
            
            # Update manipulation and misinformation flags
            if content_analysis_dict.get('fake_news'):
                result.is_misinformation = content_analysis_dict['fake_news'].get('is_fake_news', False)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            return result
            
        finally:
            file_handler.cleanup_file(temp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing URL: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    file_handler.create_directories()
    print(f"🚀 {settings.app_name} v{settings.app_version} started")
    print(f"📡 Server running on http://{settings.host}:{settings.port}")
    print(f"📚 API docs available at http://{settings.host}:{settings.port}/api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    file_handler.cleanup_temp_directory()
    print("👋 Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
