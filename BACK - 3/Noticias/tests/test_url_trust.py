from app.schemas.news import UrlHealth, UrlRiskSignal
from app.services.url_trust import build_url_trust_assessment


def test_url_trust_is_url_only_and_penalizes_shorteners() -> None:
    health = UrlHealth(
        status="redirected",
        http_status=200,
        is_reachable=True,
        is_disconnected=False,
        redirect_count=1,
    )
    signals = [
        UrlRiskSignal(
            signal="shortener_url",
            severity="media",
            explanation="Usa acortador.",
        )
    ]

    trust = build_url_trust_assessment(health, signals)

    assert trust.scope == "url_only"
    assert trust.level in {"precaucion", "riesgosa"}
