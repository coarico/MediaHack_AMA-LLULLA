from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application
    app_name: str = "AMA-LLU-IA Video/Audio Analyzer"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    
    # File Upload
    max_file_size: int = 52428800  # 50MB
    allowed_audio_formats: List[str] = ["mp3", "wav", "ogg", "m4a", "flac"]
    allowed_video_formats: List[str] = ["mp4", "avi", "mov", "mkv", "webm"]
    
    # Storage
    temp_dir: str = "./temp"
    upload_dir: str = "./uploads"
    
    # Analysis Thresholds
    audio_confidence_threshold: float = 0.7
    video_confidence_threshold: float = 0.7
    
    # CORS
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://coarico.github.io,https://amallulia.vercel.app",
        validation_alias="CORS_ORIGINS",
    )
    cors_origin_regex: str | None = None
    
    # Google APIs
    google_application_credentials: str = "./google-credentials.json"
    google_fact_check_api_key: str = ""
    
    # Speech-to-Text
    whisper_model: str = "base"  # tiny, base, small, medium, large (base balancea velocidad/precision)
    whisper_language: str = "es"

    # Speech-to-Text (Deepgram) - usado por TranscriptionService
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-2"
    deepgram_language: str = "es"
    
    # Content Analysis
    enable_fact_checking: bool = True
    enable_fake_news_detection: bool = True
    fake_news_threshold: float = 0.7

    # Groq LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    
    # yt-dlp options
    ytdlp_proxy_url: str = ""
    ytdlp_cookies_file: str = ""

    # URL downloader provider
    download_provider: str = "local"  # local | external
    download_worker_url: str = ""
    download_worker_api_key: str = ""
    download_worker_timeout_seconds: int = 120

    # Firebase Firestore
    firebase_credentials_path: str = "./Secret/base-mediahackii-dde4ddaa87de.json"
    firebase_project_id: str = "base-mediahackii"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
