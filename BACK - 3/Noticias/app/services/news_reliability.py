from app.schemas.news import (
    ContentQuality,
    CrossSourceCheck,
    NewsAnalysis,
    NewsReliabilityAssessment,
    SourceClassification,
    SourceVerification,
    UrlContentClassification,
    UrlTrustAssessment,
)


TRUSTED_SOURCE_STATUSES = {"radar_media", "registered_media", "ifcn_verified"}


def build_news_reliability_assessment(
    source_classification: SourceClassification,
    source_verification: SourceVerification,
    url_trust_assessment: UrlTrustAssessment,
    url_content_classification: UrlContentClassification,
    content_quality: ContentQuality,
    cross_source_check: CrossSourceCheck,
    analysis: NewsAnalysis,
) -> NewsReliabilityAssessment:
    score = 0
    factors: list[str] = []

    if source_verification.status == "radar_media":
        score += 30
        factors.append("La fuente esta en la lista Radar configurada.")
    elif source_verification.status == "ifcn_verified":
        score += 30
        factors.append("La fuente esta registrada como medio de verificacion.")
    elif source_verification.status == "registered_media":
        score += 25
        factors.append("La fuente coincide con el registro interno de medios confiables.")
    elif source_classification.source_name:
        score += 15
        factors.append("La fuente fue reconocida parcialmente por el clasificador.")
    else:
        factors.append("La fuente no coincide con Radar ni con el registro interno.")

    url_score = round(url_trust_assessment.score * 0.2)
    score += url_score
    factors.append(f"Confiabilidad tecnica del URL: {url_trust_assessment.score}/100.")

    quality_score = round(content_quality.quality_score * 0.2)
    score += quality_score
    factors.append(f"Calidad estructural del contenido: {content_quality.quality_score}/100.")

    credibility_score = round(analysis.credibility.score * 0.15)
    score += credibility_score
    factors.append(f"Credibilidad textual estimada: {analysis.credibility.score}/100.")

    if cross_source_check.independent_sources_count >= 2:
        score += 10
        factors.append("Hay cobertura relacionada en multiples dominios.")
    elif cross_source_check.related_coverage_count >= 1:
        score += 6
        factors.append("Hay al menos una noticia relacionada para contraste.")
    else:
        score -= 8
        factors.append("No se encontraron noticias relacionadas con la configuracion actual.")

    if not url_content_classification.is_news:
        score -= 10
        factors.append("El URL no fue clasificado como noticia estructurada.")
    else:
        score += 5
        factors.append("El URL fue clasificado como contenido noticioso.")

    score = max(0, min(100, score))
    if score >= 75:
        level = "alta"
        explanation = "La noticia tiene un contexto de fuente y estructura con alta confiabilidad operativa."
    elif score >= 50:
        level = "media"
        explanation = "La noticia tiene senales suficientes, pero conviene contrastar cobertura y evidencia."
    elif score >= 25:
        level = "baja"
        explanation = "La noticia requiere validacion adicional por fuente, estructura, URL o cobertura limitada."
    else:
        level = "indeterminada"
        explanation = "No hay suficientes senales para estimar confiabilidad de la noticia."

    return NewsReliabilityAssessment(
        score=score,
        level=level,
        is_reliable_source_context=source_verification.status in TRUSTED_SOURCE_STATUSES,
        explanation=explanation,
        factors=factors[:8],
    )
