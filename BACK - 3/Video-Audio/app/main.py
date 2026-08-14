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
file_handler = FileHandler()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
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
        temp_path = await file_handler.download_from_url(str(request.url))
        
        try:
            # Determine file type and analyze
            if file_handler.is_audio_file(temp_path):
                result = await audio_analyzer.analyze(temp_path)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file type. Please provide an audio file."
                )
            
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
