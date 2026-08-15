from app.schemas.news import ContentAttribution, CrossSourceCheck, SourceClassification
from app.services.source_verification import build_source_verification


def test_registered_media_needs_validation_when_no_related_coverage() -> None:
    source = SourceClassification(
        is_radar_media=False,
        communication_type="medio_no_radar",
        source_name="El Comercio",
        matched_domain="elcomercio.com",
        confidence=0.95,
        explanation="Registro interno",
    )
    attribution = ContentAttribution(
        platform_name="elcomercio.com",
        platform_type="sitio_web",
        publisher_name="El Comercio",
        publisher_type="medio_comunicacion",
        source_domain="elcomercio.com",
        explanation="Dominio directo",
    )
    cross = CrossSourceCheck(coverage_status="no_related_coverage")

    verification = build_source_verification(source, attribution, cross)

    assert verification.status == "registered_media"
    assert verification.needs_additional_validation is True
