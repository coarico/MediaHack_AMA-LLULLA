from urllib.parse import urlparse

from app.schemas.news import (
    SourceVerification,
    UrlContentClassification,
    UrlHealth,
    UrlRiskSignal,
    UrlTechnicalReport,
    UrlTrustAssessment,
)


REGISTERED_STATUSES = {"radar_media", "registered_media", "ifcn_verified"}


def build_url_technical_report(
    original_url: str,
    final_url: str,
    url_health: UrlHealth,
    url_trust_assessment: UrlTrustAssessment,
    url_content_classification: UrlContentClassification,
    source_verification: SourceVerification,
    url_risk_signals: list[UrlRiskSignal],
) -> UrlTechnicalReport:
    original_domain = _domain(original_url)
    final_domain = _domain(final_url)
    redirected_to_different_domain = bool(
        original_domain and final_domain and original_domain != final_domain
    )
    medium_or_high = sum(1 for signal in url_risk_signals if signal.severity in {"media", "alta"})
    is_registered_source = source_verification.status in REGISTERED_STATUSES

    recommendations: list[str] = []
    if redirected_to_different_domain:
        recommendations.append("Revisar que el dominio final corresponda al medio esperado.")
    if not url_health.is_reachable:
        recommendations.append("Reintentar o verificar manualmente porque el link no fue alcanzable.")
    if not is_registered_source:
        recommendations.append("Contrastar con fuentes registradas o documentos primarios.")
    if not url_content_classification.is_news:
        recommendations.append("Validar si el contenido corresponde a una noticia o a una publicacion social.")
    if medium_or_high:
        recommendations.append("Revisar las senales tecnicas marcadas antes de usar el contenido como evidencia.")

    if url_health.is_disconnected:
        operational_status = "requiere_revision"
        summary = "El link no esta disponible o no permite acceder al contenido."
    elif medium_or_high >= 2 or redirected_to_different_domain:
        operational_status = "requiere_revision"
        summary = "La URL tiene senales tecnicas que requieren revision manual."
    elif url_trust_assessment.score >= 75 and is_registered_source:
        operational_status = "confiable"
        summary = "La URL es alcanzable, tecnicamente estable y corresponde a una fuente registrada."
    elif url_trust_assessment.score >= 50:
        operational_status = "precaucion"
        summary = "La URL es alcanzable, pero conviene contrastar fuente, contenido o cobertura."
    else:
        operational_status = "indeterminado"
        summary = "No hay suficientes senales tecnicas para clasificar la URL con confianza."

    if not recommendations:
        recommendations.append("Mantener contraste editorial normal; este reporte no concluye verdad o falsedad.")

    return UrlTechnicalReport(
        original_domain=original_domain,
        final_domain=final_domain,
        uses_https=urlparse(final_url).scheme == "https",
        redirected_to_different_domain=redirected_to_different_domain,
        redirect_count=url_health.redirect_count,
        http_status=url_health.http_status,
        is_reachable=url_health.is_reachable,
        is_registered_source=is_registered_source,
        source_name=source_verification.source_name,
        content_kind=url_content_classification.content_kind,
        risk_signal_count=len(url_risk_signals),
        high_or_medium_risk_count=medium_or_high,
        operational_status=operational_status,
        summary=summary,
        recommendations=recommendations[:6],
    )


def _domain(url: str) -> str | None:
    parsed = urlparse(url)
    domain = (parsed.hostname or "").lower().removeprefix("www.")
    return domain or None
