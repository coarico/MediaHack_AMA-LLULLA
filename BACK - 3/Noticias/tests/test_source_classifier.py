from app.services import source_classifier
from app.services.source_classifier import classify_source


def test_classifies_radar_media(monkeypatch) -> None:
    monkeypatch.setattr(
        source_classifier,
        "_load_radar_media",
        lambda: [{"name": "Medio Radar", "domain": "medio.com"}],
    )

    result = classify_source("https://www.medio.com/noticia", "www.medio.com")

    assert result.is_radar_media is True
    assert result.communication_type == "medio_radar"
    assert result.source_name == "Medio Radar"


def test_classifies_social_media(monkeypatch) -> None:
    monkeypatch.setattr(source_classifier, "_load_radar_media", lambda: [])

    result = classify_source("https://x.com/cuenta/status/123", "x.com")

    assert result.is_radar_media is False
    assert result.communication_type == "red_social"


def test_classifies_registered_el_comercio_as_media() -> None:
    result = classify_source("https://www.elcomercio.com/actualidad/quito/noticia.html", "www.elcomercio.com")

    assert result.is_radar_media is True
    assert result.communication_type == "medio_radar"
    assert result.source_name == "El Comercio"
