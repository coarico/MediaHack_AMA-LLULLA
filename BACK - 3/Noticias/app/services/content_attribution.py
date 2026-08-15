import re
from urllib.parse import urlparse

from app.schemas.news import ContentAttribution, ExtractedArticle, SourceClassification
from app.services.source_classifier import find_registered_source


MEDIA_HANDLE_HINTS = (
    "radio",
    "noticia",
    "noticias",
    "diario",
    "prensa",
    "periodico",
    "canal",
    "tv",
    "news",
    "medio",
)


def build_content_attribution(
    original_url: str,
    article: ExtractedArticle,
    source_classification: SourceClassification,
) -> ContentAttribution:
    parsed = urlparse(original_url)
    domain = (parsed.hostname or article.source_domain or "").lower().removeprefix("www.")
    platform_type = "red_social" if source_classification.communication_type == "red_social" else "sitio_web"
    platform_name = _platform_name(domain)

    shared_by = _extract_social_handle(parsed.path) if platform_type == "red_social" else None
    if not shared_by and platform_type == "red_social":
        shared_by = _extract_handle_from_text(article.text)

    registry_match = find_registered_source(handle=shared_by) if shared_by else None
    publisher_type = _publisher_type_from_handle(shared_by, source_classification, registry_match)
    publisher_name = (
        registry_match.get("name")
        if registry_match
        else _display_name_from_handle(shared_by)
        if shared_by
        else source_classification.source_name
    )

    if platform_type == "red_social":
        explanation = (
            f"El contenido esta alojado en {platform_name}; la cuenta que lo comparte es "
            f"{shared_by or 'no identificada'}."
        )
    else:
        explanation = f"El contenido proviene directamente del dominio {article.source_domain}."

    return ContentAttribution(
        platform_name=platform_name,
        platform_type=platform_type,
        shared_by_account=shared_by,
        shared_by_display_name=publisher_name,
        publisher_name=publisher_name,
        publisher_handle=shared_by,
        publisher_type=publisher_type,
        source_domain=article.source_domain,
        explanation=explanation,
    )


def _platform_name(domain: str) -> str:
    if "instagram.com" in domain:
        return "Instagram"
    if domain in {"x.com", "twitter.com"}:
        return "X"
    if "facebook.com" in domain:
        return "Facebook"
    if "tiktok.com" in domain:
        return "TikTok"
    if "youtube.com" in domain or "youtu.be" in domain:
        return "YouTube"
    return domain or "desconocida"


def _extract_social_handle(path: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    if not parts:
        return None
    reserved = {"p", "reel", "tv", "stories", "explore", "accounts"}
    return None if parts[0].lower() in reserved else parts[0]


def _extract_handle_from_text(text: str) -> str | None:
    patterns = [
        r"\b([A-Za-z0-9._]{3,40})\s+(?:â€¢|•|·)",
        r"\b([A-Za-z0-9._]{3,40})\s+(?:\d+\s*(?:s|m|h|d|w|y|a)\b|\d+\s*(?:dia|dias|hora|horas|semana|semanas))",
    ]
    ignored = {"instagram", "facebook", "follow", "login", "signup", "close", "options"}
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            handle = match.group(1).strip()
            if handle.lower() not in ignored:
                return handle
    return None


def _publisher_type_from_handle(
    handle: str | None,
    source_classification: SourceClassification,
    registry_match: dict[str, str] | None = None,
):
    if registry_match:
        publisher_type = registry_match.get("publisher_type") or "medio_comunicacion"
        if publisher_type in {"medio_digital", "medio_tradicional"}:
            return "medio_comunicacion"
        return publisher_type
    if source_classification.communication_type != "red_social":
        if source_classification.communication_type in {"medio_radar", "medio_no_radar"}:
            return "medio_comunicacion"
        if source_classification.communication_type == "gobierno":
            return "institucion_publica"
        if source_classification.communication_type in {"institucion", "empresa", "ong"}:
            return "institucion_privada"
        return "otro"

    if not handle:
        return "desconocido"
    normalized = handle.lower()
    if any(hint in normalized for hint in MEDIA_HANDLE_HINTS):
        return "medio_comunicacion"
    return "usuario_cuenta_personal"


def _display_name_from_handle(handle: str | None) -> str | None:
    if not handle:
        return None
    return handle.replace(".", " ").replace("_", " ").strip().title()
