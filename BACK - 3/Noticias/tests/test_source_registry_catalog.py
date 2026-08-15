from app.services.source_classifier import classify_source


def test_classifies_registered_web_media():
    result = classify_source("https://www.primicias.ec/noticias/politica/demo")

    assert result.source_name == "Primicias"
    assert result.is_radar_media is True
    assert result.communication_type == "medio_radar"
    assert result.registry_category == "medio_comunicacion_sitio_web"
    assert result.platform == "sitio_web"


def test_classifies_registered_instagram_handle():
    result = classify_source("https://www.instagram.com/radiocentro.ec/")

    assert result.source_name == "Radio Centro"
    assert result.matched_handle == "radiocentro.ec"
    assert result.editorial_alignment == "alineada_gobierno"
    assert result.platform == "instagram"


def test_does_not_match_unknown_instagram_by_generic_domain():
    result = classify_source("https://www.instagram.com/cuenta_desconocida/")

    assert result.source_name is None
    assert result.communication_type == "red_social"
