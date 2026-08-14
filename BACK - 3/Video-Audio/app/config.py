import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for env_path in candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or "=" not in clean:
                continue
            key, value = clean.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _bool_env(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _list_env(key: str, default: list[str]) -> list[str]:
    value = os.getenv(key)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "AMA-LLU-IA Video/Audio Analyzer"
    app_version: str = "1.0.0"
    debug: bool = True

    host: str = "0.0.0.0"
    port: int = 8002

    max_file_size: int = 52_428_800
    allowed_audio_formats: list[str] = None
    allowed_video_formats: list[str] = None

    temp_dir: str = "./temp"
    upload_dir: str = "./uploads"

    audio_confidence_threshold: float = 0.7
    video_confidence_threshold: float = 0.7

    cors_origins: list[str] = None
    cors_origin_regex: str | None = r"https://.*(app\.github\.dev|githubpreview\.dev|vscode-cdn\.net|devtunnels\.ms)"

    google_application_credentials: str = "./google-credentials.json"
    google_fact_check_api_key: str = ""

    whisper_model: str = "base"
    whisper_language: str = "es"

    enable_fact_checking: bool = True
    enable_fake_news_detection: bool = True
    fake_news_threshold: float = 0.7

    def __post_init__(self):
        if self.allowed_audio_formats is None:
            object.__setattr__(self, "allowed_audio_formats", ["mp3", "wav", "ogg", "m4a", "flac"])
        if self.allowed_video_formats is None:
            object.__setattr__(self, "allowed_video_formats", ["mp4", "avi", "mov", "mkv", "webm"])
        if self.cors_origins is None:
            object.__setattr__(
                self,
                "cors_origins",
                ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "https://coarico.github.io"],
            )


def load_settings() -> Settings:
    _load_dotenv()
    return Settings(
        app_name=os.getenv("APP_NAME", "AMA-LLU-IA Video/Audio Analyzer"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        debug=_bool_env("DEBUG", True),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8002")),
        max_file_size=int(os.getenv("MAX_FILE_SIZE", "52428800")),
        allowed_audio_formats=_list_env("ALLOWED_AUDIO_FORMATS", ["mp3", "wav", "ogg", "m4a", "flac"]),
        allowed_video_formats=_list_env("ALLOWED_VIDEO_FORMATS", ["mp4", "avi", "mov", "mkv", "webm"]),
        temp_dir=os.getenv("TEMP_DIR", "./temp"),
        upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
        audio_confidence_threshold=float(os.getenv("AUDIO_CONFIDENCE_THRESHOLD", "0.7")),
        video_confidence_threshold=float(os.getenv("VIDEO_CONFIDENCE_THRESHOLD", "0.7")),
        cors_origins=_list_env(
            "CORS_ORIGINS",
            ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "https://coarico.github.io"],
        ),
        cors_origin_regex=os.getenv(
            "CORS_ORIGIN_REGEX",
            r"https://.*(app\.github\.dev|githubpreview\.dev|vscode-cdn\.net|devtunnels\.ms)",
        ),
        google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./google-credentials.json"),
        google_fact_check_api_key=os.getenv("GOOGLE_FACT_CHECK_API_KEY", ""),
        whisper_model=os.getenv("WHISPER_MODEL", "base"),
        whisper_language=os.getenv("WHISPER_LANGUAGE", "es"),
        enable_fact_checking=_bool_env("ENABLE_FACT_CHECKING", True),
        enable_fake_news_detection=_bool_env("ENABLE_FAKE_NEWS_DETECTION", True),
        fake_news_threshold=float(os.getenv("FAKE_NEWS_THRESHOLD", "0.7")),
    )


settings = load_settings()
