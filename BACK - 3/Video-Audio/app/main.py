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
from app.services.deepgram_service import DeepgramTranscriptionService
from app.services.content_analyzer import ContentAnalyzer
from app.services.fact_checker import FactChecker
from app.services.web_searcher import WebSearcher
from app.services.llm_analyzer import LLMAnalyzer
from app.utils.file_handler import FileHandler
from app.services.firebase_service import save_analysis_to_firestore

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
deepgram_service = DeepgramTranscriptionService()
content_analyzer = ContentAnalyzer()
fact_checker = FactChecker()
web_searcher = WebSearcher()
llm_analyzer = LLMAnalyzer()
file_handler = FileHandler()


async def perform_content_analysis(file_path: str, is_video: bool = False, source_metadata: dict = None, skip_transcription: bool = False) -> dict:
    """
    Perform complete content analysis: transcription, fake news, fact-checking,
    web search, and LLM analysis.
    
    Args:
        file_path: Path to media file
        is_video: Whether the file is a video
        source_metadata: Optional metadata from URL (title, channel, etc.)
        skip_transcription: Skip transcription if True
        
    Returns:
        dict: Content analysis results
    """
    try:
        # Transcription
        if skip_transcription:
            transcription = {'text': '', 'language': 'es', 'segments': []}
        elif is_video:
            transcription = await transcription_service.transcribe_video(file_path)
        else:
            transcription = await transcription_service.transcribe(file_path)
        
        text = transcription.get('text', '')

        # Deepgram como respaldo (si la transcripcion principal fallo/quedo vacia)
        # o como doble verificacion (si la principal funciono). No afecta el
        # flujo si DEEPGRAM_API_KEY no esta configurada.
        deepgram_backup = None
        if settings.deepgram_api_key and not skip_transcription:
            try:
                if is_video:
                    deepgram_backup = await deepgram_service.transcribe_video(file_path)
                else:
                    deepgram_backup = await deepgram_service.transcribe(file_path)
            except Exception as e:
                print(f"ℹ️ Deepgram backup/verificacion no disponible: {e}")

        if not text and deepgram_backup and deepgram_backup.get('text'):
            print("⚠️ Transcripcion principal vacia, usando Deepgram como respaldo")
            transcription = deepgram_backup
            text = transcription['text']

        if not text:
            return {
                'has_transcription': False,
                'transcription': None,
                'fake_news': None,
                'fact_checking': None,
                'extracted_claims': [],
                'web_context': None,
                'llm_analysis': None
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
            seg_count = min(len(segments), 3)
            print(f"🔍 Fact-checking {seg_count} segments...")
            for idx, segment in enumerate(segments[:3]):
                seg_text = segment.get('text', '').strip()
                if len(seg_text) < 20:
                    continue
                # Truncate to 80 chars for Google Fact Check API limit
                seg_text = seg_text[:80]
                
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

        # Adjuntar la transcripcion de Deepgram como verificacion doble
        # (solo si no fue ya usada como respaldo, es decir, si la principal si funciono)
        if deepgram_backup and deepgram_backup.get('text') and transcription is not deepgram_backup:
            transcription['deepgram_backup'] = deepgram_backup

        # Web search for related sources
        print("🌐 Searching web for related sources...")
        web_context = None
        try:
            # Build search query from title or transcription
            if source_metadata and source_metadata.get('title'):
                # Clean title: remove channel suffix after | or -, limit to 80 chars
                raw_title = source_metadata['title']
                search_query = raw_title.split('|')[0].split(' - ')[0].strip()
                if len(search_query) > 80:
                    search_query = search_query[:80].strip()
            else:
                # Use first 100 chars of transcription as query
                search_query = text[:100].strip()
            
            articles = await web_searcher.search_news(search_query, max_results=8)
            
            # If no news results, try general search
            if not articles:
                print("📰 News search empty, trying general search...")
                articles = await web_searcher.search_general(search_query, max_results=8)
            
            print(f"📰 Total articles found: {len(articles)}")
            
            # Cross-reference with reliable sources
            cross_ref = web_searcher._cross_reference(text, articles)
            
            web_context = {
                'articles': articles,
                'total_articles_found': len(articles),
                'cross_reference': cross_ref
            }
        except Exception as e:
            print(f"⚠️ Web search failed: {e}")
            web_context = None

        # LLM Analysis
        print("🤖 Running LLM analysis...")
        llm_analysis = None
        try:
            title = source_metadata.get('title', '') if source_metadata else ''
            channel = source_metadata.get('channel', '') if source_metadata else ''
            llm_analysis = await llm_analyzer.analyze_transcription(
                transcription=text,
                title=title,
                channel=channel,
                web_articles=web_context.get('articles', []) if web_context else None
            )
            if llm_analysis:
                print(f"✅ LLM verdict: {llm_analysis.get('veredicto', 'N/A')}")
        except Exception as e:
            print(f"⚠️ LLM analysis failed: {e}")

        return {
            'has_transcription': True,
            'transcription': transcription,
            'fake_news': fake_news,
            'fact_checking': fact_checking,
            'extracted_claims': extracted_claims,
            'web_context': web_context,
            'llm_analysis': llm_analysis,
            'llm_verdict': llm_analysis.get('veredicto') if llm_analysis else None,
            'llm_confidence': llm_analysis.get('confianza') if llm_analysis else None,
        }
        
    except Exception as e:
        print(f"⚠️ Content analysis failed: {e}")
        return {
            'has_transcription': False,
            'transcription': None,
            'fake_news': None,
            'fact_checking': None,
            'extracted_claims': [],
            'web_context': None,
            'llm_analysis': None
        }


def _combine_verdicts(result, content_analysis_dict):
    """Combine video/audio analyzer verdict with LLM verdict"""
    llm_verdict = (content_analysis_dict.get('llm_verdict') or '').upper() if content_analysis_dict else ''
    llm_confidence = content_analysis_dict.get('llm_confidence') or 0 if content_analysis_dict else 0
    llm_analysis = content_analysis_dict.get('llm_analysis', {}) if content_analysis_dict else {}
    indicios_ia = (llm_analysis.get('indicios_ia', '') or '').lower() if llm_analysis else ''
    
    if not llm_verdict:
        return
    
    # Check if LLM detected AI generation indicators
    has_ai_indicators = indicios_ia and 'no se detectaron' not in indicios_ia
    
    # LLM says FALSO or likely AI-generated
    if llm_verdict in ['FALSO', 'FALSIFICADO', 'ENGAÑOSO', 'IA_GENERADO']:
        # Override: LLM detected it's fake/AI even if video metrics didn't
        if not result.is_ai_generated:
            print(f"🔧 LLM override: marking as AI-generated (LLM verdict: {llm_verdict}, {llm_confidence}%)")
            result.is_ai_generated = True
            # Blend confidence: weight LLM confidence more if video said real
            llm_conf = llm_confidence / 100.0 if llm_confidence > 1 else llm_confidence
            result.confidence = max(result.confidence, llm_conf * 0.7 + 0.3)
    # LLM detected AI indicators even if verdict is MIXTO
    elif has_ai_indicators and llm_verdict in ['MIXTO']:
        if not result.is_ai_generated:
            print(f"🔧 LLM AI indicators detected: {indicios_ia[:80]}")
            result.is_ai_generated = True
            llm_conf = llm_confidence / 100.0 if llm_confidence > 1 else llm_confidence
            result.confidence = max(result.confidence, llm_conf * 0.5 + 0.3)
    elif llm_verdict in ['AUTÉNTICO', 'VERDADERO', 'REAL'] and llm_confidence >= 80 and not has_ai_indicators:
        # LLM is very confident it's real, boost the real score
        if not result.is_ai_generated:
            llm_conf = llm_confidence / 100.0 if llm_confidence > 1 else llm_confidence
            result.confidence = min(result.confidence * 0.7 + llm_conf * 0.3, 0.95)
            print(f"🔧 LLM boost: confidence adjusted to {result.confidence:.2f} (LLM: {llm_verdict}, {llm_confidence}%)")


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
            
            # Combine verdicts: video metrics + LLM
            _combine_verdicts(result, content_analysis_dict)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Save to Firestore
            try:
                result_dict = result.model_dump()
                result_dict['processing_time'] = processing_time
                result_dict['metadata'] = {**result_dict.get('metadata', {}), 'filename': file.filename}
                save_analysis_to_firestore(result_dict)
            except Exception as fs_err:
                print(f"⚠️ Firestore save failed (non-blocking): {fs_err}")
            
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

            # Combine verdicts: video metrics + LLM
            _combine_verdicts(result, content_analysis_dict)

            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time

            # Save to Firestore
            try:
                result_dict = result.model_dump()
                result_dict['processing_time'] = processing_time
                result_dict['metadata'] = {**result_dict.get('metadata', {}), 'filename': file.filename}
                save_analysis_to_firestore(result_dict)
            except Exception as fs_err:
                print(f"⚠️ Firestore save failed (non-blocking): {fs_err}")

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
            content_analysis_dict = await perform_content_analysis(temp_path, is_video=is_video, source_metadata=source_metadata, skip_transcription=request.skip_transcription if hasattr(request, 'skip_transcription') else False)
            from app.models.schemas import ContentAnalysisResult
            result.content_analysis = ContentAnalysisResult(**content_analysis_dict)
            
            # Update manipulation and misinformation flags
            if content_analysis_dict.get('fake_news'):
                result.is_misinformation = content_analysis_dict['fake_news'].get('is_fake_news', False)
            
            # Combine verdicts: video/audio metrics + LLM
            _combine_verdicts(result, content_analysis_dict)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            # Save to Firestore with source metadata
            try:
                result_dict = result.model_dump()
                result_dict['processing_time'] = processing_time
                save_analysis_to_firestore(result_dict, source_metadata=source_metadata)
            except Exception as fs_err:
                print(f"⚠️ Firestore save failed (non-blocking): {fs_err}")
            
            return result
            
        finally:
            file_handler.cleanup_file(temp_path)
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        print(f"❌ URL ENDPOINT ERROR: {e}")
        traceback.print_exc()
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
