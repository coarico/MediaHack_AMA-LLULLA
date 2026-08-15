import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
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


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    cors_origins_raw: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    fact_check_api_key: str | None = None
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    firestore_collection: str = "contentAnalyses"
    google_search_api_key: str | None = None
    google_search_cx: str | None = None
    request_timeout_seconds: float = 12
    max_html_bytes: int = 2_000_000
    max_article_chars: int = 24_000
    related_news_limit: int = 6

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        cors_origins_raw=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
        cors_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        fact_check_api_key=os.getenv("FACT_CHECK_API_KEY") or os.getenv("GOOGLE_FACT_CHECK_API_KEY") or None,
        firebase_project_id=os.getenv("FIREBASE_PROJECT_ID") or None,
        firebase_credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None,
        firestore_collection=os.getenv("FIRESTORE_ANALYSES_COLLECTION", "contentAnalyses"),
        google_search_api_key=os.getenv("GOOGLE_SEARCH_API_KEY") or None,
        google_search_cx=os.getenv("GOOGLE_SEARCH_CX") or None,
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "12")),
        max_html_bytes=int(os.getenv("MAX_HTML_BYTES", "2000000")),
        max_article_chars=int(os.getenv("MAX_ARTICLE_CHARS", "24000")),
        related_news_limit=int(os.getenv("RELATED_NEWS_LIMIT", "6")),
    )


settings = get_settings()
