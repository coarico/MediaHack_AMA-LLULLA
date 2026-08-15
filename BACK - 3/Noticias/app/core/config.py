import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


LLM_PROVIDERS = {"auto", "groq", "openai", "none"}
DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _load_dotenv() -> None:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    loaded_paths = set()
    for env_path in candidates:
        resolved_path = env_path.resolve()
        if resolved_path in loaded_paths:
            continue
        loaded_paths.add(resolved_path)
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or "=" not in clean:
                continue
            key, value = clean.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    cors_origins_raw: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = None
    llm_provider: str = "auto"
    llm_fallback_on_error: bool = True
    openai_api_key: str | None = None
    openai_model: str = DEFAULT_OPENAI_MODEL
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    fact_check_api_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = DEFAULT_GROQ_MODEL
    groq_base_url: str = DEFAULT_GROQ_BASE_URL
    firebase_project_id: str | None = None
    firebase_credentials_path: str | None = None
    firestore_collection: str = "contentAnalyses"
    firestore_transport: str = "rest"
    google_search_api_key: str | None = None
    google_search_cx: str | None = None
    gdelt_enabled: bool = True
    gdelt_timespan: str = "3months"
    gdelt_max_records: int = 10
    gdelt_query_limit: int = 5
    gdelt_timeout_seconds: float = 5
    news_rss_enabled: bool = True
    news_rss_query_limit: int = 3
    news_rss_timeout_seconds: float = 6
    duckduckgo_fallback_query_limit: int = 2
    duckduckgo_timeout_seconds: float = 4
    request_timeout_seconds: float = 12
    max_html_bytes: int = 2_000_000
    max_article_chars: int = 24_000
    related_news_limit: int = 6
    related_source_search_limit: int = 12

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    _load_dotenv()
    llm_provider = _env("LLM_PROVIDER", "auto").lower()
    if llm_provider not in LLM_PROVIDERS:
        raise RuntimeError(f"LLM_PROVIDER invalido: {llm_provider}. Usa auto, groq, openai o none.")
    return Settings(
        app_env=_env("APP_ENV", "local"),
        cors_origins_raw=_env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
        cors_origin_regex=_env_optional("CORS_ORIGIN_REGEX"),
        llm_provider=llm_provider,
        llm_fallback_on_error=_env_bool("LLM_FALLBACK_ON_ERROR", True),
        openai_api_key=_env_optional("OPENAI_API_KEY"),
        openai_model=_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        gemini_api_key=_env_optional("GEMINI_API_KEY") or _env_optional("GOOGLE_API_KEY"),
        gemini_model=_env("GEMINI_MODEL", "gemini-2.0-flash"),
        fact_check_api_key=_env_optional("FACT_CHECK_API_KEY") or _env_optional("GOOGLE_FACT_CHECK_API_KEY"),
        groq_api_key=_env_optional("GROQ_API_KEY"),
        groq_model=_env("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        groq_base_url=_env("GROQ_BASE_URL", DEFAULT_GROQ_BASE_URL),
        firebase_project_id=_env_optional("FIREBASE_PROJECT_ID"),
        firebase_credentials_path=_env_optional("GOOGLE_APPLICATION_CREDENTIALS"),
        firestore_collection=_env("FIRESTORE_ANALYSES_COLLECTION", "contentAnalyses"),
        firestore_transport=_env("FIRESTORE_TRANSPORT", "rest").lower(),
        google_search_api_key=_env_optional("GOOGLE_SEARCH_API_KEY"),
        google_search_cx=_env_optional("GOOGLE_SEARCH_CX"),
        gdelt_enabled=_env_bool("GDELT_ENABLED", True),
        gdelt_timespan=_env("GDELT_TIMESPAN", "3months"),
        gdelt_max_records=int(_env("GDELT_MAX_RECORDS", "10")),
        gdelt_query_limit=int(_env("GDELT_QUERY_LIMIT", "5")),
        gdelt_timeout_seconds=float(_env("GDELT_TIMEOUT_SECONDS", "5")),
        news_rss_enabled=_env_bool("NEWS_RSS_ENABLED", True),
        news_rss_query_limit=int(_env("NEWS_RSS_QUERY_LIMIT", "3")),
        news_rss_timeout_seconds=float(_env("NEWS_RSS_TIMEOUT_SECONDS", "6")),
        duckduckgo_fallback_query_limit=int(_env("DUCKDUCKGO_FALLBACK_QUERY_LIMIT", "2")),
        duckduckgo_timeout_seconds=float(_env("DUCKDUCKGO_TIMEOUT_SECONDS", "4")),
        request_timeout_seconds=float(_env("REQUEST_TIMEOUT_SECONDS", "12")),
        max_html_bytes=int(_env("MAX_HTML_BYTES", "2000000")),
        max_article_chars=int(_env("MAX_ARTICLE_CHARS", "24000")),
        related_news_limit=int(_env("RELATED_NEWS_LIMIT", "6")),
        related_source_search_limit=int(_env("RELATED_SOURCE_SEARCH_LIMIT", "12")),
    )


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()


def _env_optional(key: str) -> str | None:
    value = os.environ.get(key)
    if value is None:
        return None
    clean = value.strip()
    return clean or None


def _env_bool(key: str, default: bool) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si"}


settings = get_settings()
