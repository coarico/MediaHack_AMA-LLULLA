from app.schemas.news import ContentAttribution, ContentQuality, ExtractedArticle, SourceClassification
from app.services.url_content_classifier import classify_url_content


def test_classifies_registered_media_article_as_news() -> None:
    result = classify_url_content(
        "https://www.elcomercio.com/actualidad/quito/inseguridad.html",
        _article("Inseguridad preocupa en Quito", "Texto informativo. " * 40),
        _source("medio_no_radar"),
        _attribution("sitio_web"),
        _quality(has_date=True, text_length=720),
    )

    assert result.is_news is True
    assert result.content_kind == "noticia"


def test_classifies_instagram_post_as_social_publication() -> None:
    result = classify_url_content(
        "https://www.instagram.com/p/demo/",
        _article("Instagram", "radiocentro.ec publico una declaracion."),
        _source("red_social"),
        _attribution("red_social"),
        _quality(has_date=False, text_length=39),
    )

    assert result.is_news is False
    assert result.content_kind == "publicacion_red_social"


def test_classifies_social_media_post_from_media_account_as_news() -> None:
    result = classify_url_content(
        "https://www.instagram.com/p/demo/",
        _article(
            "Instagram",
            (
                "radiocentro.ec 1d El ministro respondio a cuestionamientos durante una entrevista "
                "y explico las medidas anunciadas por el Gobierno."
            ),
        ),
        _source("red_social"),
        _attribution("red_social", publisher_type="medio_comunicacion", publisher_name="Radio Centro"),
        _quality(has_date=False, text_length=132),
    )

    assert result.is_news is True
    assert result.content_kind == "noticia"


def _article(title: str, text: str) -> ExtractedArticle:
    return ExtractedArticle(
        url="https://example.com",
        source_domain="example.com",
        title=title,
        text=text,
    )


def _source(communication_type: str) -> SourceClassification:
    return SourceClassification(
        is_radar_media=False,
        communication_type=communication_type,
        source_name="El Comercio" if communication_type != "red_social" else None,
        matched_domain="elcomercio.com" if communication_type != "red_social" else None,
        confidence=0.95,
        explanation="Test",
    )


def _attribution(
    platform_type: str,
    publisher_type: str = "medio_comunicacion",
    publisher_name: str = "El Comercio",
) -> ContentAttribution:
    return ContentAttribution(
        platform_name="Instagram" if platform_type == "red_social" else "elcomercio.com",
        platform_type=platform_type,
        publisher_name=publisher_name,
        publisher_type=publisher_type,
        source_domain="example.com",
        explanation="Test",
    )


def _quality(has_date: bool, text_length: int) -> ContentQuality:
    return ContentQuality(
        has_author=False,
        has_date=has_date,
        text_length=text_length,
        has_sources=False,
        title_body_overlap_score=0.4,
        quality_score=70,
        warnings=[],
    )
