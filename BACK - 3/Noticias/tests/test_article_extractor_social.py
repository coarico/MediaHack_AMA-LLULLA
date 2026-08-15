from app.services.article_extractor import extract_article


def test_extract_article_allows_short_social_publication() -> None:
    html = """
    <html>
      <head><title>Instagram</title></head>
      <body>
        radiocentro.ec 1d El ministro respondio a cuestionamientos durante una entrevista publica.
      </body>
    </html>
    """

    article = extract_article("https://www.instagram.com/p/demo/", html)

    assert article.title == "Instagram"
    assert "radiocentro.ec" in article.text
