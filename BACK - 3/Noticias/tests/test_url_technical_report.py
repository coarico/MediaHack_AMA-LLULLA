from app.schemas.news import (
    SourceVerification,
    UrlContentClassification,
    UrlHealth,
    UrlRiskSignal,
    UrlTrustAssessment,
)
from app.services.url_technical_report import build_url_technical_report


def test_url_technical_report_marks_registered_https_url_as_reliable() -> None:
    report = build_url_technical_report(
        "https://www.elcomercio.com/noticia",
        "https://www.elcomercio.com/noticia",
        UrlHealth(status="active", http_status=200, is_reachable=True, is_disconnected=False),
        UrlTrustAssessment(is_technically_trustworthy=True, level="confiable", score=100),
        UrlContentClassification(is_news=True, content_kind="noticia", confidence=95),
        SourceVerification(
            status="registered_media",
            source_name="El Comercio",
            needs_additional_validation=False,
            recommendation="Test",
        ),
        [],
    )

    assert report.operational_status == "confiable"
    assert report.uses_https is True
    assert report.is_registered_source is True


def test_url_technical_report_requires_review_when_final_domain_changes() -> None:
    report = build_url_technical_report(
        "https://bit.ly/demo",
        "https://example-news.com/noticia",
        UrlHealth(status="redirected", http_status=200, is_reachable=True, is_disconnected=False, redirect_count=1),
        UrlTrustAssessment(is_technically_trustworthy=True, level="confiable", score=80),
        UrlContentClassification(is_news=True, content_kind="noticia", confidence=75),
        SourceVerification(
            status="unknown",
            source_name=None,
            needs_additional_validation=True,
            recommendation="Test",
        ),
        [
            UrlRiskSignal(
                signal="redirect_to_different_domain",
                severity="baja",
                explanation="La URL termina en un dominio distinto al dominio original.",
            )
        ],
    )

    assert report.redirected_to_different_domain is True
    assert report.operational_status == "requiere_revision"
