from app.schemas.news import (
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
    EntitySet,
    ExtractedArticle,
    NewsAnalysis,
    SentimentAnalysis,
)
from app.services.gender_impact import assess_gender_impact


def test_gender_impact_returns_no_signal_for_neutral_news() -> None:
    assessment = assess_gender_impact(
        _article("Cierre vial en Quito", "La via registra congestion por trabajos de mantenimiento."),
        _analysis(),
    )

    assert assessment.status == "sin_senales_relevantes"
    assert assessment.signals == []


def test_gender_impact_flags_review_signal() -> None:
    assessment = assess_gender_impact(
        _article("Declaraciones politicas", "La candidata fue atacada con la frase mujer tenia que ser."),
        _analysis(),
    )

    assert assessment.status == "senales_para_revision"
    assert assessment.signals[0].signal_type == "estereotipos_genero"


def test_gender_impact_flags_alert_when_multiple_high_signals() -> None:
    assessment = assess_gender_impact(
        _article(
            "Ataques contra candidata",
            "La candidata denuncio amenaza y montaje con contenido sexual para desacreditar a una mujer.",
        ),
        _analysis(),
    )

    assert assessment.status == "alerta_impacto_genero"
    assert assessment.requires_specialized_review is True


def _article(title: str, text: str) -> ExtractedArticle:
    return ExtractedArticle(
        url="https://example.com/news",
        source_domain="example.com",
        title=title,
        text=text,
    )


def _analysis() -> NewsAnalysis:
    return NewsAnalysis(
        summary="Resumen",
        topic="politica",
        category="noticias",
        main_claims=[],
        entities=EntitySet(),
        keywords=[],
        search_queries=[],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=0, direction="neutral", explanation="Sin sesgo"),
        manipulation_signals=[],
        clickbait=ClickbaitAnalysis(score=0, evidence=[]),
        credibility=CredibilityAnalysis(score=80, risk_level="bajo", explanation="Estructura basica"),
        information_gaps=[],
        missing_context=[],
        recommendation="Revisar contexto.",
    )
