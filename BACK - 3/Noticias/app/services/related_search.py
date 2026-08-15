from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.news import NewsAnalysis, RelatedNewsItem
from app.services.source_classifier import classify_source


async def search_related_news(analysis: NewsAnalysis, original_url: str) -> list[RelatedNewsItem]:
    queries = analysis.search_queries or [" ".join(analysis.keywords[:5])]
    results: list[RelatedNewsItem] = []
    seen_urls = {original_url}

    if not settings.google_search_api_key or not settings.google_search_cx:
        return _search_public_related_news(queries, seen_urls, results)

    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            for query in queries[:3]:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": settings.google_search_api_key,
                        "cx": settings.google_search_cx,
                        "q": query,
                        "num": min(settings.related_news_limit, 10),
                    },
                )
                response.raise_for_status()
                payload = response.json()

                for item in payload.get("items", []):
                    url = item.get("link")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    results.append(_build_related_item(item.get("title") or "Sin titulo", url, item.get("snippet"), query))
                    if len(results) >= settings.related_news_limit:
                        return results
    except Exception:
        return _search_public_related_news(queries, seen_urls, results)

    if results:
        return results
    return _search_public_related_news(queries, seen_urls, results)


def _search_public_related_news(queries: list[str], seen_urls: set[str], results: list[RelatedNewsItem]) -> list[RelatedNewsItem]:
    for query in queries[:3]:
        for item in _search_public_web(query):
            if item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            results.append(item)
            if len(results) >= settings.related_news_limit:
                return results
    return results


def _search_public_web(query: str) -> list[RelatedNewsItem]:
    if not query.strip():
        return []

    search_url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
    request = Request(
        search_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AMA-LLU-IA/1.0; news-analysis)",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    parser = _DuckDuckGoResultParser()
    parser.feed(html)
    results: list[RelatedNewsItem] = []
    for raw_title, raw_url, snippet in parser.results[: settings.related_news_limit]:
        url = _clean_duckduckgo_url(raw_url)
        if not url:
            continue
        results.append(_build_related_item(raw_title, url, snippet, query))
    return results


def _build_related_item(title: str, url: str, snippet: str | None, query: str) -> RelatedNewsItem:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    source_classification = classify_source(url, domain)
    return RelatedNewsItem(
        title=title or "Sin titulo",
        url=url,
        source=domain or None,
        source_name=source_classification.source_name,
        source_type=source_classification.communication_type,
        source_registry_status=_source_registry_status(source_classification),
        source_confidence_score=round(source_classification.confidence * 100),
        snippet=snippet,
        relation_reason=f"Relacionada por busqueda: {query}",
    )


def _clean_duckduckgo_url(raw_url: str) -> str | None:
    if not raw_url:
        return None
    decoded = unquote(unescape(raw_url))
    parsed = urlparse(decoded)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        return unquote(target) if target else None
    if parsed.scheme in {"http", "https"}:
        return decoded
    return None


def _source_registry_status(source_classification) -> str:
    if source_classification.is_radar_media:
        return "radar"
    if source_classification.source_name:
        return "registro interno"
    if source_classification.communication_type in {"medio_no_radar", "gobierno", "institucion"}:
        return "medio no registrado"
    return "sin registro"


class _DuckDuckGoResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[tuple[str, str, str | None]] = []
        self._capture_title = False
        self._capture_snippet = False
        self._current_title: list[str] = []
        self._current_url: str | None = None
        self._current_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        class_name = attr_map.get("class") or ""
        if tag == "a" and "result__a" in class_name:
            self._capture_title = True
            self._current_title = []
            self._current_url = attr_map.get("href")
            self._current_snippet = []
        elif tag in {"a", "div"} and "result__snippet" in class_name:
            self._capture_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_title:
            self._capture_title = False
            title = " ".join("".join(self._current_title).split())
            if title and self._current_url:
                self.results.append((unescape(title), self._current_url, None))
        elif tag in {"a", "div"} and self._capture_snippet:
            self._capture_snippet = False
            if self.results:
                title, url, _ = self.results[-1]
                snippet = " ".join("".join(self._current_snippet).split())
                self.results[-1] = (title, url, unescape(snippet) if snippet else None)

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._current_title.append(data)
        elif self._capture_snippet:
            self._current_snippet.append(data)
