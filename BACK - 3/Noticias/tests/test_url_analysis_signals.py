from app.schemas.news import ExtractedArticle, RelatedNewsItem, UrlHealth
from app.services.claims_extractor import extract_verifiable_claims
from app.services.content_quality import evaluate_content_quality
from app.services.cross_source import build_cross_source_check
from app.services.url_risk import evaluate_url_risk


def test_detects_shortener_url_signal() -> None:
    health = UrlHealth(
        status="redirected",
        http_status=200,
        is_reachable=True,
        is_disconnected=False,
        redirect_count=1,
    )

    signals = evaluate_url_risk("https://bit.ly/demo", "https://example.com/noticia", health)

    assert any(signal.signal == "shortener_url" for signal in signals)


def test_detects_redirect_to_different_domain_signal() -> None:
    health = UrlHealth(
        status="redirected",
        http_status=200,
        is_reachable=True,
        is_disconnected=False,
        redirect_count=1,
    )

    signals = evaluate_url_risk("https://example.com/noticia", "https://otro-dominio.com/noticia", health)

    assert any(signal.signal == "redirect_to_different_domain" for signal in signals)


def test_content_quality_flags_missing_author_and_sources() -> None:
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Titulo de prueba",
        text="Texto breve sin referencias. " * 30,
    )

    quality = evaluate_content_quality(article)

    assert quality.has_author is False
    assert quality.has_sources is False
    assert quality.quality_score < 100


def test_extracts_verifiable_claims_with_numbers() -> None:
    article = ExtractedArticle(
        url="https://example.com/noticia",
        source_domain="example.com",
        title="Titulo",
        text="El candidato obtuvo 42% de apoyo en la encuesta publicada por la organizacion.",
    )

    claims = extract_verifiable_claims(article)

    assert claims
    assert claims[0].type == "estadistica"


def test_cross_source_multiple_domains() -> None:
    related = [
        RelatedNewsItem(title="A", url="https://a.com/news", source="a.com"),
        RelatedNewsItem(title="B", url="https://b.com/news", source="b.com"),
    ]

    result = build_cross_source_check(related)

    assert result.coverage_status == "multiple_sources"
    assert result.independent_sources_count == 2
