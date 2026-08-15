from app.schemas.news import ExtractedArticle, SourceClassification
from app.services.content_attribution import build_content_attribution


def test_instagram_attribution_detects_media_account_from_text() -> None:
    article = ExtractedArticle(
        url="https://www.instagram.com/p/demo/",
        source_domain="www.instagram.com",
        title="Instagram",
        text="radiocentro.ec • 1d El ministro dio declaraciones sobre elecciones.",
    )
    source = SourceClassification(
        is_radar_media=False,
        communication_type="red_social",
        confidence=0.95,
        explanation="Red social",
    )

    attribution = build_content_attribution("https://www.instagram.com/p/demo/", article, source)

    assert attribution.platform_name == "Instagram"
    assert attribution.shared_by_account == "radiocentro.ec"
    assert attribution.publisher_name == "Radio Centro"
    assert attribution.publisher_type == "medio_comunicacion"
