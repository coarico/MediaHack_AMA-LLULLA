from app.schemas.news import (
    AnalyzeRequest,
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
    ContentAttribution,
    ExtractedArticle,
    NewsAnalysis,
    SentimentAnalysis,
    SourceClassification,
)
from app.services.editorial_metadata import build_editorial_metadata


def test_infers_editorial_metadata_for_media_source() -> None:
    request = AnalyzeRequest(url="https://example.com/noticia")
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Elecciones",
        published_at="14/08/2026",
        text="Texto de prueba " * 80,
    )
    source = SourceClassification(
        is_radar_media=True,
        communication_type="medio_radar",
        source_name="Example",
        matched_domain="example.com",
        confidence=1,
        explanation="Radar",
    )
    analysis = NewsAnalysis(
        summary="Resumen",
        topic="Elecciones y fraude",
        category="politica",
        keywords=["elecciones", "fraude"],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=10, direction="no determinado", explanation=""),
        clickbait=ClickbaitAnalysis(score=0),
        credibility=CredibilityAnalysis(score=80, risk_level="bajo", explanation=""),
        recommendation="Verificar",
    )

    metadata = build_editorial_metadata(request, article, source, analysis)

    assert metadata.platform == "sitio_web"
    assert metadata.publisher_type == "medio_comunicacion"
    assert metadata.publication_date == "14/08/2026"
    assert metadata.thematic_axis == "Elecciones (fraude)"


def test_infers_social_publication_date_from_relative_marker() -> None:
    request = AnalyzeRequest(url="https://www.instagram.com/p/demo/")
    article = ExtractedArticle(
        url="https://www.instagram.com/p/demo/",
        source_domain="www.instagram.com",
        title="Instagram",
        text="radiocentro.ec 1d El ministro dio declaraciones.",
    )
    source = SourceClassification(
        is_radar_media=False,
        communication_type="red_social",
        confidence=0.95,
        explanation="Red social",
    )
    attribution = ContentAttribution(
        platform_name="Instagram",
        platform_type="red_social",
        shared_by_account="radiocentro.ec",
        shared_by_display_name="Radio Centro",
        publisher_name="Radio Centro",
        publisher_type="medio_comunicacion",
        source_domain="instagram.com",
        explanation="Test",
    )

    metadata = build_editorial_metadata(request, article, source, _analysis(), attribution)

    assert metadata.platform == "red_social"
    assert metadata.publication_date is not None
    assert "T" in metadata.publication_date
    assert any("red social" in note for note in metadata.notes)


def _analysis() -> NewsAnalysis:
    return NewsAnalysis(
        summary="Resumen",
        topic="Politica",
        category="noticias",
        keywords=[],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=10, direction="no determinado", explanation=""),
        clickbait=ClickbaitAnalysis(score=0),
        credibility=CredibilityAnalysis(score=80, risk_level="bajo", explanation=""),
        recommendation="Verificar",
    )
