from app.schemas.news import ExtractedArticle, VerifiableClaim
from app.services.llm_context import build_llm_compact_context, compact_context_to_prompt


def test_build_llm_compact_context_reduces_long_article() -> None:
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Inseguridad en la Simon Bolivar preocupa a Quito",
        published_at="2026-08-14",
        text=(
            "La avenida Simon Bolivar registra hechos violentos recientes en Quito. "
            "Conductores reportaron cierres y problemas de seguridad vial. "
            "La Policia informo que 120 agentes participaron en procedimientos. "
            "Vecinos pidieron mas controles en varios tramos. "
        )
        * 30,
    )

    context = build_llm_compact_context(article)

    assert context.original_text_chars > context.compact_text_chars
    assert context.estimated_tokens > 0
    assert len(context.top_sentences) <= 8
    assert "Inseguridad" in compact_context_to_prompt(context)


def test_build_llm_compact_context_keeps_candidate_claims() -> None:
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Titulo",
        text="El candidato afirmo que construyo 120 centros durante su gestion.",
    )
    claims = [
        VerifiableClaim(
            claim="El candidato afirmo que construyo 120 centros durante su gestion.",
            type="estadistica",
        )
    ]

    context = build_llm_compact_context(article, claims)

    assert context.candidate_claims == [claims[0].claim]
