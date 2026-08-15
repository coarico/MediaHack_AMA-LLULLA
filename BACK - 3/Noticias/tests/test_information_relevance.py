from app.schemas.news import (
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
    ExtractedArticle,
    NewsAnalysis,
    SentimentAnalysis,
)
from app.services.information_relevance import classify_information_relevance


def test_classifies_election_fraud_as_relevant() -> None:
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Denuncian fraude electoral",
        text="La campana denuncio posible fraude en el conteo de votos.",
    )
    analysis = NewsAnalysis(
        summary="Resumen",
        topic="Fraude electoral en conteo de votos",
        category="politica",
        keywords=["fraude", "votos", "elecciones"],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=10, direction="no determinado", explanation=""),
        clickbait=ClickbaitAnalysis(score=0),
        credibility=CredibilityAnalysis(score=70, risk_level="medio", explanation=""),
        recommendation="Verificar",
    )

    relevance = classify_information_relevance(article, analysis)

    assert relevance.is_relevant is True
    assert relevance.domain == "electoral"
    assert "fraude_electoral" in relevance.subtopics


def test_security_news_without_election_context_is_not_electoral() -> None:
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Inseguridad preocupa a conductores y vecinos",
        text="La avenida registra hechos violentos, procedimientos policiales y preocupacion por seguridad.",
    )
    analysis = NewsAnalysis(
        summary="Resumen",
        topic="Inseguridad en Quito",
        category="seguridad",
        keywords=["inseguridad", "seguridad", "quito"],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=10, direction="no determinado", explanation=""),
        clickbait=ClickbaitAnalysis(score=0),
        credibility=CredibilityAnalysis(score=70, risk_level="medio", explanation=""),
        recommendation="Verificar",
    )

    relevance = classify_information_relevance(article, analysis)

    assert relevance.is_relevant is False
    assert relevance.domain == "no_electoral"
    assert relevance.subtopics == []
