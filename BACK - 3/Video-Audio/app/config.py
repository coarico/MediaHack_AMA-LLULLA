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
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "https://coarico.github.io"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
