from app.schemas.news import (
    AnalyzeRequest,
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
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

