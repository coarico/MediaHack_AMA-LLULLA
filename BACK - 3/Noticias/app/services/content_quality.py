import re

from app.schemas.news import ContentQuality, ExtractedArticle


SOURCE_PATTERNS = (
    "segun",
    "de acuerdo con",
    "fuente",
    "informe",
    "documento",
    "comunicado",
    "declaracion",
    "boletin",
    "reporte",
)


def evaluate_content_quality(article: ExtractedArticle) -> ContentQuality:
    text = article.text.strip()
    warnings: list[str] = []
    has_author = bool(article.author)
    has_date = bool(article.published_at)
    has_sources = any(pattern in _normalize(text) for pattern in SOURCE_PATTERNS)
    overlap_score = _title_body_overlap(article.title or "", text)

    score = 100
    if len(text) < 900:
        score -= 25
        warnings.append("El texto extraido es corto para un analisis robusto.")
    if not has_author:
        score -= 15
        warnings.append("No se detecto autor o redaccion responsable.")
    if not has_date:
        score -= 15
        warnings.append("No se detecto fecha de publicacion.")
    if not has_sources:
        score -= 20
        warnings.append("No se detectaron referencias claras a fuentes, documentos o informes.")
    if overlap_score < 0.15:
        score -= 10
        warnings.append("El titulo tiene baja coincidencia lexical con el cuerpo extraido.")
    if _has_sensational_style(article.title or ""):
        score -= 10
        warnings.append("El titulo usa senales de estilo sensacionalista.")

    return ContentQuality(
        has_author=has_author,
        has_date=has_date,
        text_length=len(text),
        has_sources=has_sources,
        title_body_overlap_score=overlap_score,
        quality_score=max(0, min(100, score)),
        warnings=warnings,
    )


def _title_body_overlap(title: str, text: str) -> float:
    title_words = {
        word for word in re.findall(r"\b\w{4,}\b", _normalize(title)) if word not in {"para", "sobre", "entre"}
    }
    if not title_words:
        return 0
    body_words = set(re.findall(r"\b\w{4,}\b", _normalize(text[:2000])))
    return len(title_words & body_words) / len(title_words)


def _has_sensational_style(title: str) -> bool:
    normalized = _normalize(title)
    return "!" in title or any(word in normalized for word in ["urgente", "impactante", "escandalo", "ultima hora"])


def _normalize(value: str) -> str:
    return value.lower()

