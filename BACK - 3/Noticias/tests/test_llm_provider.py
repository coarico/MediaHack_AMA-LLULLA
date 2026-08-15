from types import SimpleNamespace

from app.schemas.news import ExtractedArticle
from app.services import ai_analyzer
from app.services.llm_context import build_llm_compact_context


def test_resolve_provider_prefers_groq_in_auto(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_analyzer,
        "settings",
        SimpleNamespace(
            llm_provider="auto",
            groq_api_key="groq-key",
            openai_api_key="openai-key",
        ),
    )

    assert ai_analyzer._resolve_provider() == "groq"


def test_resolve_provider_uses_openai_when_requested(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_analyzer,
        "settings",
        SimpleNamespace(
            llm_provider="openai",
            groq_api_key="groq-key",
            openai_api_key="openai-key",
        ),
    )

    assert ai_analyzer._resolve_provider() == "openai"


def test_resolve_provider_returns_none_without_requested_key(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_analyzer,
        "settings",
        SimpleNamespace(
            llm_provider="groq",
            groq_api_key=None,
            openai_api_key="openai-key",
        ),
    )

    assert ai_analyzer._resolve_provider() is None


def test_resolve_provider_strict_raises_without_requested_key(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_analyzer,
        "settings",
        SimpleNamespace(
            llm_provider="groq",
            groq_api_key=None,
            openai_api_key=None,
        ),
    )

    try:
        ai_analyzer._resolve_provider(strict=True)
    except RuntimeError as exc:
        assert "GROQ_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing GROQ_API_KEY error")


def test_groq_analyzer_uses_standard_http_without_openai_sdk(monkeypatch) -> None:
    calls = {}

    monkeypatch.setattr(
        ai_analyzer,
        "settings",
        SimpleNamespace(
            groq_api_key="groq-key",
            groq_base_url="https://api.groq.com/openai/v1",
            groq_model="llama-3.1-8b-instant",
            request_timeout_seconds=12,
        ),
    )

    def fake_post(payload):
        calls["payload"] = payload
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"summary":"Resumen","topic":"Tema","category":"noticias",'
                            '"main_claims":[],"entities":{"people":[],"organizations":[],"locations":[]},'
                            '"keywords":["via publica"],"search_queries":["consulta llm especifica"],'
                            '"sentiment":{"label":"neutral","score":0.5},'
                            '"bias_analysis":{"score":0,"direction":"neutral","explanation":"Test"},'
                            '"manipulation_signals":[],"clickbait":{"score":0,"evidence":[]},'
                            '"credibility":{"score":80,"risk_level":"bajo","explanation":"Test"},'
                            '"information_gaps":[],"missing_context":[],"recommendation":"Contrastar."}'
                        )
                    }
                }
            ]
        }

    monkeypatch.setattr(ai_analyzer, "_post_groq_completion", fake_post)

    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Titulo",
        text="Texto de prueba para analizar noticia.",
    )
    context = build_llm_compact_context(article)

    import asyncio

    analysis = asyncio.run(ai_analyzer._analyze_with_groq(article, context))

    assert calls["payload"]["model"] == "llama-3.1-8b-instant"
    assert analysis.summary == "Resumen"
    assert analysis.search_queries[0] == "consulta llm especifica"
    assert "via publica" not in [keyword.lower() for keyword in analysis.keywords]


def test_analyze_article_falls_back_when_groq_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_analyzer,
        "settings",
        SimpleNamespace(
            llm_provider="groq",
            groq_api_key="groq-key",
            groq_model="llama-3.1-8b-instant",
            llm_fallback_on_error=True,
        ),
    )
    monkeypatch.setattr(
        ai_analyzer,
        "_analyze_with_groq",
        lambda article, compact_context: _async_raise(RuntimeError("Error Groq HTTP 403: error code: 1010")),
    )
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Titulo",
        text="Texto de prueba para analizar noticia con suficiente contenido local. " * 10,
    )

    import asyncio

    analysis, metadata = asyncio.run(ai_analyzer.analyze_article_with_metadata(article))

    assert analysis.summary
    assert any("Groq HTTP 403" in item for item in analysis.missing_context)
    assert metadata.provider == "groq"
    assert metadata.status == "fallback"


async def _async_raise(exc):
    raise exc
