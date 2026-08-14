from app.schemas.news import ExtractedArticle
from app.services.keyword_extractor import extract_keywords, infer_category_from_keywords


def test_extract_keywords_prioritizes_title_and_accents():
    article = ExtractedArticle(
        url="https://www.elcomercio.com/actualidad/quito/inseguridad-simon-bolivar.html",
        final_url="https://www.elcomercio.com/actualidad/quito/inseguridad-simon-bolivar.html",
        title="Inseguridad en la Simón Bolívar preocupa a conductores y vecinos de Quito",
        text=(
            "La avenida Simon Bolivar enfrenta nuevos desafios de seguridad que ponen bajo la lupa "
            "varios tramos. Conductores y vecinos reportan problemas de movilidad y seguridad vial."
        ),
        source_domain="www.elcomercio.com",
        authors=[],
        published_at=None,
        language="es",
    )

    keywords = extract_keywords(article)

    assert "Simón Bolívar" in keywords
    assert "inseguridad" in keywords
    assert "conductores" in keywords
    assert "Quito" in keywords
    assert "seguridad vial" in keywords
    assert infer_category_from_keywords(keywords) == "seguridad/movilidad"
