import re
from datetime import datetime, timedelta, timezone

from app.schemas.news import AnalyzeRequest, ContentAttribution, EditorialMetadata, ExtractedArticle, NewsAnalysis, SourceClassification


SOCIAL_TYPES = {"red_social"}
PUBLIC_TYPES = {"gobierno"}
PRIVATE_INSTITUTION_TYPES = {"empresa", "ong", "institucion"}
MEDIA_TYPES = {"medio_radar", "medio_no_radar"}


def build_editorial_metadata(
    request: AnalyzeRequest,
    article: ExtractedArticle,
    source_classification: SourceClassification,
    analysis: NewsAnalysis,
    content_attribution: ContentAttribution | None = None,
) -> EditorialMetadata:
    notes: list[str] = []
    inferred = not any(
        [
            request.platform,
            request.publisher_type,
            request.publication_date,
            request.thematic_axis,
        ]
    )

    platform = request.platform or _infer_platform(source_classification)
    if not request.platform:
        notes.append("Plataforma inferida desde el tipo de fuente.")

    publisher_type = request.publisher_type or (content_attribution.publisher_type if content_attribution else None) or _infer_publisher_type(source_classification)
    if not request.publisher_type:
        notes.append("Quien publica fue inferido desde la clasificacion de fuente.")

    social_publication_date = (
        _extract_social_publication_date(article.text)
        if content_attribution and content_attribution.platform_type == "red_social"
        else None
    )
    publication_date = request.publication_date or article.published_at or social_publication_date
    if not request.publication_date and article.published_at:
        notes.append("Fecha tomada de la metadata extraida del articulo.")
    elif not request.publication_date and social_publication_date:
        notes.append("Fecha aproximada inferida desde marca temporal de red social.")
    elif not publication_date:
        notes.append("No se detecto fecha de publicacion.")

    thematic_axis = request.thematic_axis or _infer_thematic_axis(analysis)
    if not request.thematic_axis:
        notes.append("Eje tematico inferido desde categoria, tema y palabras clave.")

    confidence = 0.95 if not inferred else 0.7
    if not publication_date:
        confidence -= 0.15
    if source_classification.communication_type == "desconocido":
        confidence -= 0.15

    return EditorialMetadata(
        platform=platform,
        publisher_type=publisher_type,
        publication_date=publication_date,
        thematic_axis=thematic_axis,
        thematic_tags=_thematic_tags(analysis),
        inferred=inferred,
        confidence=max(0, min(1, confidence)),
        notes=notes,
    )


def _infer_platform(source_classification: SourceClassification):
    if source_classification.communication_type in SOCIAL_TYPES:
        return "red_social"
    if source_classification.communication_type == "desconocido":
        return "desconocido"
    return "sitio_web"


def _infer_publisher_type(source_classification: SourceClassification):
    communication_type = source_classification.communication_type
    if communication_type in MEDIA_TYPES:
        return "medio_comunicacion"
    if communication_type in PUBLIC_TYPES:
        return "institucion_publica"
    if communication_type in PRIVATE_INSTITUTION_TYPES:
        return "institucion_privada"
    if communication_type == "red_social":
        return "usuario_cuenta_personal"
    if communication_type == "desconocido":
        return "desconocido"
    return "otro"


def _infer_thematic_axis(analysis: NewsAnalysis) -> str:
    text = " ".join([analysis.topic, analysis.category, *analysis.keywords]).lower()
    axis = "Elecciones"
    tags = []
    if "fraude" in text:
        tags.append("fraude")
    if "narcotrafico" in text or "narcotráfico" in text:
        tags.append("narcotrafico")
    if tags:
        return f"{axis} ({' - '.join(tags)})"
    if "eleccion" in text or "electoral" in text or "voto" in text:
        return axis
    return analysis.category or "Sin clasificar"


def _thematic_tags(analysis: NewsAnalysis) -> list[str]:
    text = " ".join([analysis.topic, analysis.category, *analysis.keywords]).lower()
    tags = []
    for tag in ["elecciones", "fraude", "narcotrafico", "campana", "votacion", "seguridad"]:
        if tag in text or (tag == "narcotrafico" and "narcotráfico" in text):
            tags.append(tag)
    return tags


def _extract_social_publication_date(text: str) -> str | None:
    match = re.search(
        r"\b(?P<amount>\d{1,3})\s*(?P<unit>s|m|h|d|w|y|a|dia|dias|hora|horas|semana|semanas)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None

    amount = int(match.group("amount"))
    unit = match.group("unit").lower()
    if unit == "s":
        delta = timedelta(seconds=amount)
    elif unit == "m":
        delta = timedelta(minutes=amount)
    elif unit in {"h", "hora", "horas"}:
        delta = timedelta(hours=amount)
    elif unit in {"d", "dia", "dias"}:
        delta = timedelta(days=amount)
    elif unit in {"w", "semana", "semanas"}:
        delta = timedelta(weeks=amount)
    else:
        delta = timedelta(days=365 * amount)

    return (datetime.now(timezone.utc) - delta).isoformat()
