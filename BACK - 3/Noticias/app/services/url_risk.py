from urllib.parse import parse_qs, urlparse

from app.schemas.news import UrlHealth, UrlRiskSignal


SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "buff.ly",
    "cutt.ly",
    "is.gd",
    "rebrand.ly",
}


def evaluate_url_risk(original_url: str, final_url: str, url_health: UrlHealth) -> list[UrlRiskSignal]:
    signals: list[UrlRiskSignal] = []
    parsed_original = urlparse(original_url)
    parsed_final = urlparse(final_url)
    domain = (parsed_final.hostname or "").lower().removeprefix("www.")
    original_domain = (parsed_original.hostname or "").lower().removeprefix("www.")

    if original_domain in SHORTENERS:
        signals.append(
            UrlRiskSignal(
                signal="shortener_url",
                severity="media",
                explanation="La URL usa un acortador y oculta el destino final hasta resolverla.",
            )
        )

    if url_health.redirect_count >= 2:
        signals.append(
            UrlRiskSignal(
                signal="multiple_redirects",
                severity="media",
                explanation="La URL redirige varias veces antes de llegar al contenido final.",
            )
        )

    if original_domain and domain and original_domain != domain:
        severity = "baja" if url_health.redirect_count <= 1 else "media"
        signals.append(
            UrlRiskSignal(
                signal="redirect_to_different_domain",
                severity=severity,
                explanation="La URL termina en un dominio distinto al dominio original.",
            )
        )

    if url_health.is_disconnected:
        signals.append(
            UrlRiskSignal(
                signal="disconnected_url",
                severity="alta",
                explanation="El link no esta disponible o no permite acceder al contenido.",
            )
        )

    if domain.count("-") >= 2 or sum(char.isdigit() for char in domain) >= 3:
        signals.append(
            UrlRiskSignal(
                signal="unusual_domain_pattern",
                severity="media",
                explanation="El dominio tiene un patron poco comun con varios guiones o numeros.",
            )
        )

    query_params = parse_qs(parsed_final.query)
    if len(query_params) >= 8:
        signals.append(
            UrlRiskSignal(
                signal="many_tracking_parameters",
                severity="baja",
                explanation="La URL contiene muchos parametros; podria provenir de una campana o enlace rastreado.",
            )
        )

    if parsed_final.scheme != "https":
        signals.append(
            UrlRiskSignal(
                signal="not_https",
                severity="media",
                explanation="La noticia no usa HTTPS en la URL final.",
            )
        )

    return signals
