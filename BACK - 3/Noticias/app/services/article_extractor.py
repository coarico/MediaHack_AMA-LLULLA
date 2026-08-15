import html
import json
import re
from urllib.parse import urlparse

from app.core.config import settings
from app.schemas.news import ExtractedArticle


class ExtractionError(RuntimeError):
    pass


def extract_article(url: str, html_content: str) -> ExtractedArticle:
    extracted = _extract_with_trafilatura(url, html_content) or _extract_with_fallback(html_content)
    text = (extracted.get("text") or "").strip()
    if len(text) < _minimum_text_length(url):
        raise ExtractionError("La noticia tiene muy poco contenido para analizarla bien.")

    parsed = urlparse(url)
    return ExtractedArticle(
        url=url,
        source_domain=parsed.netloc.lower(),
        title=extracted.get("title"),
        author=extracted.get("author"),
        published_at=extracted.get("date"),
        language=extracted.get("language"),
        image_url=extracted.get("image"),
        text=text[: settings.max_article_chars],
    )


def _minimum_text_length(url: str) -> int:
    domain = (urlparse(url).hostname or "").lower()
    if any(social in domain for social in ("instagram.com", "facebook.com", "x.com", "twitter.com", "tiktok.com", "threads.net")):
        return 80
    return 300


def _extract_with_trafilatura(url: str, html_content: str) -> dict | None:
    try:
        import trafilatura
    except ModuleNotFoundError:
        return None

    downloaded = trafilatura.extract(
        html_content,
        url=url,
        output_format="json",
        include_comments=False,
        include_tables=False,
        with_metadata=True,
    )
    if not downloaded:
        return None
    return json.loads(downloaded)


def _extract_with_fallback(html_content: str) -> dict:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, flags=re.IGNORECASE | re.DOTALL)
    title = (
        _meta_content(html_content, "og:title")
        or _meta_content(html_content, "twitter:title")
        or (_clean_text(title_match.group(1)) if title_match else None)
    )
    author = _meta_content(html_content, "author") or _jsonld_value(html_content, "author")
    published_at = (
        _meta_content(html_content, "article:published_time")
        or _meta_content(html_content, "datePublished")
        or _jsonld_value(html_content, "datePublished")
    )
    image = _meta_content(html_content, "og:image") or _meta_content(html_content, "twitter:image")
    language = _html_lang(html_content)

    body = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html_content, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r"<[^>]+>", " ", body)
    text = _clean_text(body)
    return {
        "title": title,
        "author": author,
        "date": published_at,
        "image": image,
        "language": language,
        "text": text,
    }


def _meta_content(html_content: str, key: str) -> str | None:
    patterns = [
        rf'<meta[^>]+(?:property|name)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(key)}["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _clean_text(match.group(1))
    return None


def _jsonld_value(html_content: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]+)"', html_content, flags=re.IGNORECASE)
    if match:
        return _clean_text(match.group(1))
    return None


def _html_lang(html_content: str) -> str | None:
    match = re.search(r"<html[^>]+lang=[\"']([^\"']+)[\"']", html_content, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _clean_text(value: str) -> str:
    clean = html.unescape(value)
    clean = re.sub(r"\s+", " ", clean).strip()
    boilerplate_patterns = [
        r"Instagram Log In Sign Up Close",
        r"By continuing, you agree to Instagram's Terms of Use and Privacy Policy",
        r"Sign up Log in",
        r"More options",
        r"Follow",
    ]
    for pattern in boilerplate_patterns:
        clean = re.sub(pattern, " ", clean, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", clean).strip()
