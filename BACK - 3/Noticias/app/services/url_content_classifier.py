from urllib.parse import urlparse

from app.schemas.news import (
    ContentAttribution,
    ContentQuality,
    ExtractedArticle,
    SourceClassification,
    UrlContentClassification,
)


VIDEO_DOMAINS = {"youtube.com", "youtu.be", "vimeo.com", "twitch.tv", "soundcloud.com", "spotify.com"}
SOCIAL_KINDS = {"red_social"}
MEDIA_KINDS = {"medio_radar", "medio_no_radar"}


def classify_url_content(
    url: str,
    article: ExtractedArticle,
    source_classification: SourceClassification,
    content_attribution: ContentAttribution,
    content_quality: ContentQuality,
) -> UrlContentClassification:
    domain = _domain(url)
    reasons: list[str] = []

    if _matches(domain, VIDEO_DOMAINS):
        return UrlContentClassification(
            is_news=False,
            content_kind="video_audio",
            confidence=90,
            reasons=["El dominio corresponde a una plataforma de video o audio."],
        )

    if content_attribution.platform_type in SOCIAL_KINDS or source_classification.communication_type == "red_social":
        text_length = len(article.text or "")
        is_media_publisher = content_attribution.publisher_type == "medio_comunicacion"
        has_informative_text = text_length >= 80
        if is_media_publisher and has_informative_text:
            confidence = 85
            reasons.append("La URL esta alojada en red social, pero la cuenta corresponde a un medio de comunicacion.")
            reasons.append("La publicacion tiene texto suficiente para tratarse como contenido noticioso.")
            return UrlContentClassification(
                is_news=True,
                content_kind="noticia",
                confidence=confidence,
                reasons=reasons,
            )
        confidence = 70 if has_informative_text else 55
        if has_informative_text:
            reasons.append("La publicacion contiene texto informativo, pero no proviene de una cuenta clasificada como medio.")
        else:
            reasons.append("El contenido esta alojado en una red social y no tiene texto suficiente de noticia.")
        return UrlContentClassification(
            is_news=False,
            content_kind="publicacion_red_social",
            confidence=confidence,
            reasons=reasons,
        )

    if source_classification.communication_type in MEDIA_KINDS:
        confidence = 75
        reasons.append("El dominio pertenece a un medio de comunicacion registrado o detectado.")
        if article.title:
            confidence += 10
            reasons.append("Se encontro titulo de articulo.")
        if content_quality.has_date:
            confidence += 5
            reasons.append("Se encontro fecha de publicacion.")
        if len(article.text or "") >= 300:
            confidence += 10
            reasons.append("El cuerpo extraido tiene extension compatible con una noticia.")
        return UrlContentClassification(
            is_news=True,
            content_kind="noticia",
            confidence=min(confidence, 100),
            reasons=reasons,
        )

    if article.title and len(article.text or "") >= 450 and content_quality.quality_score >= 45:
        return UrlContentClassification(
            is_news=True,
            content_kind="noticia",
            confidence=65,
            reasons=["El contenido tiene titulo, cuerpo y estructura compatible con articulo informativo."],
        )

    if article.title or article.text:
        return UrlContentClassification(
            is_news=False,
            content_kind="otro",
            confidence=55,
            reasons=["Se pudo extraer contenido, pero no hay senales suficientes de noticia estructurada."],
        )

    return UrlContentClassification(
        is_news=False,
        content_kind="indeterminado",
        confidence=30,
        reasons=["No se obtuvo contenido suficiente para clasificar el tipo de URL."],
    )


def _domain(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower().removeprefix("www.")


def _matches(domain: str, candidates: set[str]) -> bool:
    return any(domain == candidate or domain.endswith(f".{candidate}") for candidate in candidates)
