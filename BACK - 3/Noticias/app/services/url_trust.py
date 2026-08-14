from app.schemas.news import UrlHealth, UrlRiskSignal, UrlTrustAssessment


def build_url_trust_assessment(url_health: UrlHealth, url_risk_signals: list[UrlRiskSignal]) -> UrlTrustAssessment:
    score = 100
    reasons: list[str] = []

    if not url_health.is_reachable or url_health.is_disconnected:
        score -= 70
        reasons.append("El link no es alcanzable o esta desconectado.")
    if url_health.status == "blocked":
        score -= 45
        reasons.append("El sitio bloquea el acceso automatico al contenido.")
    if url_health.redirect_count:
        score -= min(25, url_health.redirect_count * 8)
        reasons.append("La URL redirige antes de llegar al contenido final.")

    for signal in url_risk_signals:
        if signal.severity == "alta":
            score -= 30
        elif signal.severity == "media":
            score -= 18
        else:
            score -= 8
        reasons.append(signal.explanation)

    score = max(0, min(100, score))
    if score >= 75:
        level = "confiable"
    elif score >= 50:
        level = "precaucion"
    elif score >= 1:
        level = "riesgosa"
    else:
        level = "indeterminada"

    if not reasons:
        reasons.append("No se detectaron senales tecnicas fuertes de riesgo en la URL.")

    return UrlTrustAssessment(
        is_technically_trustworthy=score >= 75,
        level=level,
        score=score,
        reasons=reasons[:8],
    )
