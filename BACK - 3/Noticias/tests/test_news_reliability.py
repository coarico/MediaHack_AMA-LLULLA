from app.schemas.news import (
    ClickbaitAnalysis,
    ContentQuality,
    CredibilityAnalysis,
    CrossSourceCheck,
    EntitySet,
    NewsAnalysis,
    SentimentAnalysis,
    SourceClassification,
    SourceVerification,
    UrlContentClassification,
    UrlTrustAssessment,
)
from app.services.news_reliability import build_news_reliability_assessment


def test_registered_media_receives_high_reliability_context() -> None:
    result = build_news_reliability_assessment(
        _source("medio_no_radar", source_name="El Comercio"),
        _verification("registered_media", "El Comercio"),
        UrlTrustAssessment(is_technically_trustworthy=True, level="confiable", score=100),
        UrlContentClassification(is_news=True, content_kind="noticia", confidence=90),
        _quality(85),
        CrossSourceCheck(related_coverage_count=2, independent_sources_count=2, coverage_status="multiple_sources"),
        _analysis(85),
    )

    assert result.score >= 75
    assert result.level == "alta"
    assert result.is_reliable_source_context is True


def test_unknown_source_without_coverage_receives_low_reliability_context() -> None:
    result = build_news_reliability_assessment(
        _source("otro"),
        _verification("unknown", None),
        UrlTrustAssessment(is_technically_trustworthy=False, level="precaucion", score=45),
        UrlContentClassification(is_news=False, content_kind="publicacion_red_social", confidence=60),
        _quality(35),
        CrossSourceCheck(related_coverage_count=0, independent_sources_count=0, coverage_status="no_related_coverage"),
        _analysis(40),
    )

    assert result.score < 50
    assert result.level in {"baja", "indeterminada"}
    assert result.is_reliable_source_context is False


def _source(communication_type: str, source_name: str | None = None) -> SourceClassification:
    return SourceClassification(
        is_radar_media=False,
        communication_type=communication_type,
        source_name=source_name,
        matched_domain="elcomercio.com" if source_name else None,
        confidence=0.95 if source_name else 0.4,
        explanation="Test",
    )


def _verification(status: str, source_name: str | None) -> SourceVerification:
    return SourceVerification(
        status=status,
        source_name=source_name,
        needs_additional_validation=status not in {"radar_media", "registered_media", "ifcn_verified"},
        recommendation="Test",
    )


def _quality(score: int) -> ContentQuality:
    return ContentQuality(
        has_author=True,
        has_date=True,
        text_length=800,
        has_sources=False,
        title_body_overlap_score=0.5,
        quality_score=score,
    )


def _analysis(score: int) -> NewsAnalysis:
    return NewsAnalysis(
        summary="Resumen",
        topic="noticias",
        category="noticias",
        main_claims=[],
        entities=EntitySet(),
        keywords=[],
        search_queries=[],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis={"score": 0, "direction": "neutral", "explanation": "Test"},
        manipulation_signals=[],
        clickbait=ClickbaitAnalysis(score=0, evidence=[]),
        credibility=CredibilityAnalysis(score=score, risk_level="bajo", explanation="Test"),
        information_gaps=[],
        missing_context=[],
        recommendation="Contrastar.",
    )
