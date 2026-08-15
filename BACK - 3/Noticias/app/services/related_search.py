from html import unescape
from html.parser import HTMLParser
from dataclasses import dataclass
import re
import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.news import NewsAnalysis, RelatedNewsItem
from app.services.source_classifier import classify_source, list_registered_sources_for_search


@dataclass(frozen=True)
class SearchQuery:
    query: str
    relation_reason: str


_STOPWORDS = {
    "actualidad",
    "avanzan",
    "ante",
    "bajo",
    "como",
    "con",
    "contra",
    "cuando",
    "comercio",
    "desde",
    "donde",
    "durante",
    "ecuador",
    "entre",
    "esta",
    "este",
    "estos",
    "hacia",
    "hasta",
    "para",
    "pero",
    "porque",
    "preocupa",
    "publica",
    "publicas",
    "publico",
    "publicos",
    "sobre",
    "tras",
    "via",
}

_ELECTORAL_TERMS = {
    "acuerdos",
    "alianzas",
    "asamblea",
    "campana",
    "candidato",
    "candidatos",
    "candidatura",
    "candidaturas",
    "cne",
    "comicios",
    "electoral",
    "electorales",
    "eleccion",
    "elecciones",
    "partido",
    "partidos",
    "politico",
    "politicos",
    "postulacion",
    "postulaciones",
    "postulante",
    "postulantes",
    "votacion",
    "voto",
}

_ECUADOR_CONTEXT_TERMS = {
    "asamblea",
    "contraloria",
    "cne",
    "ecuador",
    "ecuatoriano",
    "ecuatorianos",
    "quito",
}

_BROAD_TOPIC_TERMS = {
    "2025",
    "2026",
    "2027",
    "2028",
    "campana",
    "cne",
    "comicios",
    "ecuador",
    "electoral",
    "electorales",
    "eleccion",
    "elecciones",
    "votacion",
    "voto",
}


async def search_related_news(analysis: NewsAnalysis, original_url: str) -> list[RelatedNewsItem]:
    results: list[RelatedNewsItem] = []
    async for batch in iter_related_news_batches(analysis, original_url, min_batch_size=settings.related_news_limit):
        results.extend(batch)
        if len(results) >= settings.related_news_limit:
            return results[: settings.related_news_limit]
    return results


async def iter_related_news_batches(
    analysis: NewsAnalysis,
    original_url: str,
    min_batch_size: int = 2,
):
    queries = build_related_search_queries(analysis)
    public_related_queries = build_public_related_queries(analysis, queries)
    results: list[RelatedNewsItem] = []
    seen_urls = {original_url}
    seen_titles = {_normalize(analysis.topic)}

    if settings.gdelt_enabled:
        async for batch in _iter_gdelt_batches(queries, seen_urls, min_batch_size):
            filtered_batch = _filter_related_items(batch, seen_titles, analysis)
            if not filtered_batch:
                continue
            results.extend(filtered_batch)
            yield filtered_batch
            if len(results) >= settings.related_news_limit:
                return

    if settings.news_rss_enabled:
        for query in public_related_queries[: settings.news_rss_query_limit]:
            batch: list[RelatedNewsItem] = []
            for item in _search_news_rss(query.query, query.relation_reason):
                prepared_item = _prepare_related_item(item, analysis)
                if (
                    not prepared_item
                    or item.url in seen_urls
                    or _is_duplicate_title(item.title, seen_titles)
                ):
                    continue
                seen_urls.add(item.url)
                seen_titles.add(_normalize(_strip_source_suffix(item.title)))
                results.append(prepared_item)
                batch.append(prepared_item)
                if len(results) >= settings.related_news_limit:
                    if batch:
                        yield batch
                    return
                if len(batch) >= min_batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

    for query in public_related_queries[: settings.duckduckgo_fallback_query_limit]:
        batch: list[RelatedNewsItem] = []
        for item in _search_public_web(query.query, query.relation_reason):
            prepared_item = _prepare_related_item(item, analysis)
            if (
                not prepared_item
                or item.url in seen_urls
                or _is_duplicate_title(item.title, seen_titles)
            ):
                continue
            seen_urls.add(item.url)
            seen_titles.add(_normalize(_strip_source_suffix(item.title)))
            results.append(prepared_item)
            batch.append(prepared_item)
            if len(results) >= settings.related_news_limit:
                if batch:
                    yield batch
                return
            if len(batch) >= min_batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


async def _search_gdelt_queries(queries: list[SearchQuery], seen_urls: set[str]) -> list[RelatedNewsItem]:
    results: list[RelatedNewsItem] = []
    async for batch in _iter_gdelt_batches(queries, seen_urls, settings.related_news_limit):
        results.extend(batch)
        if len(results) >= settings.related_news_limit:
            return results
    return results


async def _iter_gdelt_batches(queries: list[SearchQuery], seen_urls: set[str], min_batch_size: int = 2):
    results: list[RelatedNewsItem] = []
    batch: list[RelatedNewsItem] = []
    for query in queries[: settings.gdelt_query_limit]:
        gdelt_query = _to_gdelt_query(query.query)
        if not gdelt_query:
            continue
        payload = _fetch_gdelt(gdelt_query)
        for article in payload.get("articles", []):
            if not article.get("url"):
                continue
            item = _build_gdelt_item(article, query.relation_reason)
            if item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            results.append(item)
            batch.append(item)
            if len(results) >= settings.related_news_limit:
                if batch:
                    yield batch
                return
            if len(batch) >= min_batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def _fetch_gdelt(query: str) -> dict:
    import json

    search_url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(
        {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "datedesc",
            "timespan": settings.gdelt_timespan,
            "maxrecords": min(settings.gdelt_max_records, settings.related_news_limit),
        }
    )
    request = Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AMA-LLU-IA/1.0; news-analysis)"},
    )
    try:
        with urlopen(request, timeout=settings.gdelt_timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8", errors="ignore"))
    except Exception:
        return {}


def _to_gdelt_query(query: str) -> str:
    clean = " ".join(query.split())
    match = re.match(r"^site:([^\s]+)\s+(.+)$", clean, flags=re.IGNORECASE)
    if not match:
        return clean[:260]

    target = match.group(1).strip()
    terms = match.group(2).strip()
    if "/" in target:
        domain, handle = target.split("/", 1)
        handle_term = handle.replace("/", " ").strip()
        return f"domainis:{domain} {handle_term} {terms}"[:260]
    return f"domainis:{target} {terms}"[:260]


def _build_gdelt_item(article: dict, relation_reason: str) -> RelatedNewsItem:
    title = article.get("title") or "Sin titulo"
    url = article.get("url") or ""
    domain = article.get("domain")
    snippet = article.get("seendate")
    return _build_related_item(
        title=title,
        url=url,
        snippet=f"GDELT seendate: {snippet}" if snippet else None,
        relation_reason=f"GDELT gratuito - {relation_reason}",
        published_at=article.get("seendate"),
        source_domain=domain,
    )


def _search_news_rss(query: str, relation_reason: str) -> list[RelatedNewsItem]:
    if not query.strip():
        return []

    search_url = "https://news.google.com/rss/search?" + urlencode(
        {"q": query, "hl": "es-419", "gl": "EC", "ceid": "EC:es-419"}
    )
    request = Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; AMA-LLU-IA/1.0; news-analysis)"},
    )
    try:
        with urlopen(request, timeout=settings.news_rss_timeout_seconds) as response:
            payload = response.read()
    except Exception:
        return []

    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    results: list[RelatedNewsItem] = []
    for item in root.findall("./channel/item")[: settings.related_news_limit]:
        title = item.findtext("title") or "Sin titulo"
        url = item.findtext("link") or ""
        if not url:
            continue
        published_at = item.findtext("pubDate")
        source_label = _extract_source_from_rss_item(title, item)
        results.append(
            _build_rss_related_item(
                title=title,
                url=url,
                source_label=source_label,
                snippet=None,
                relation_reason=f"RSS gratuito - {relation_reason}",
                published_at=published_at,
            )
        )
    return results


def _build_rss_related_item(
    title: str,
    url: str,
    source_label: str | None,
    snippet: str | None,
    relation_reason: str,
    published_at: str | None,
) -> RelatedNewsItem:
    registered_source = _find_registered_source_by_name(source_label)
    if registered_source and registered_source.get("domain"):
        return _build_related_item(
            title=title,
            url=url,
            snippet=snippet,
            relation_reason=relation_reason,
            published_at=published_at,
            source_domain=registered_source["domain"],
        )

    parsed = urlparse(url)
    return RelatedNewsItem(
        title=title,
        url=url,
        source=parsed.netloc.lower() or None,
        source_name=source_label,
        source_type="otro",
        source_registry_status="sin registro",
        source_confidence_score=45 if source_label else None,
        snippet=snippet,
        published_at=published_at,
        relation_reason=relation_reason,
    )


def build_related_search_queries(analysis: NewsAnalysis) -> list[SearchQuery]:
    base_terms = _base_terms(analysis)
    if not base_terms:
        return []

    queries: list[SearchQuery] = []
    general_terms = _general_terms(analysis)
    if general_terms:
        queries.append(SearchQuery(query=general_terms, relation_reason=f"Busqueda general GDELT: {general_terms}"))

    keyword_query = " ".join(analysis.keywords[:6]).strip()
    if keyword_query and keyword_query.lower() != general_terms.lower():
        queries.append(SearchQuery(query=keyword_query, relation_reason=f"Busqueda general por palabras clave: {keyword_query}"))

    for source in list_registered_sources_for_search(settings.related_source_search_limit):
        source_query = _source_query(base_terms, source)
        if source_query:
            queries.append(source_query)

    for query in (analysis.search_queries or []):
        if query.strip():
            queries.append(SearchQuery(query=query.strip(), relation_reason=f"Busqueda general: {query.strip()}"))

    return _dedupe_queries(queries)


def build_public_related_queries(analysis: NewsAnalysis, existing_queries: list[SearchQuery] | None = None) -> list[SearchQuery]:
    queries: list[SearchQuery] = []

    for query in _short_general_queries(analysis):
        queries.append(SearchQuery(query=query, relation_reason=f"Consulta relacionada con la noticia ingresada: {query}"))

    for query in existing_queries or []:
        if not query.query.lower().startswith("site:"):
            queries.append(query)

    for query in existing_queries or []:
        if query.query.lower().startswith("site:"):
            queries.append(query)

    return _dedupe_queries(queries)


def _base_terms(analysis: NewsAnalysis) -> str:
    candidates = []
    if analysis.topic:
        candidates.append(analysis.topic)
    candidates.extend(analysis.main_claims[:2])
    if analysis.keywords:
        candidates.append(" ".join(analysis.keywords[:5]))

    compact = " ".join(candidates)
    compact = " ".join(compact.split())
    return compact[:220]


def _general_terms(analysis: NewsAnalysis) -> str:
    keywords = [keyword for keyword in analysis.keywords if len(keyword) > 3]
    if keywords:
        return " ".join(_ranked_terms(analysis)[:6])[:180]
    return (analysis.topic or " ".join(analysis.main_claims[:1]))[:180].strip()


def _short_general_queries(analysis: NewsAnalysis) -> list[str]:
    ranked_terms = _ranked_terms(analysis)
    phrases = [term for term in ranked_terms if " " in term]
    single_terms = [term for term in ranked_terms if " " not in term]
    locations = [location for location in analysis.entities.locations if len(location) > 2]
    if not locations:
        locations = [term for term in ranked_terms if _looks_like_location(term)]

    queries: list[str] = []
    topic_query = _compact_topic_query(analysis.topic)
    if _is_electoral_analysis(analysis) and topic_query:
        queries.append(topic_query)

    for phrase in phrases[:2]:
        if locations and _normalize(phrase) != _normalize(locations[0]):
            queries.append(f'"{phrase}" {locations[0]}')
        queries.append(phrase)

    if locations:
        for term in single_terms[:3]:
            if _normalize(term) != _normalize(locations[0]):
                queries.append(f"{term} {locations[0]}")

    if len(ranked_terms) >= 2:
        queries.append(" ".join(ranked_terms[:3]))

    if analysis.topic:
        queries.append(topic_query)

    return [query for query in _dedupe_text(queries) if len(query) >= 6][:6]


def _ranked_terms(analysis: NewsAnalysis) -> list[str]:
    candidates = []
    candidates.extend(analysis.keywords)
    candidates.extend(analysis.entities.locations)
    candidates.append(analysis.topic)

    ranked: list[str] = []
    for candidate in candidates:
        clean = _clean_term(candidate)
        if not clean:
            continue
        normalized = _normalize(clean)
        tokens = _title_tokens(normalized)
        if normalized in _STOPWORDS or len(normalized) <= 3 or not tokens:
            continue
        ranked.append(clean)
    return _dedupe_text(ranked)


def _compact_topic_query(topic: str) -> str:
    words = [_clean_term(word) for word in re.split(r"\s+", topic)]
    terms = [word for word in words if word and _normalize(word) not in _STOPWORDS and len(_normalize(word)) > 3]
    return " ".join(_dedupe_text(terms)[:7])[:140]


def _clean_term(value: str | None) -> str:
    if not value:
        return ""
    clean = re.sub(r"[^\w\s-]", " ", value, flags=re.UNICODE)
    return " ".join(clean.split()).strip()


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.lower().strip()


def _looks_like_location(term: str) -> bool:
    normalized = _normalize(term)
    return normalized in {"quito", "guayaquil", "cuenca", "ecuador"}


def _dedupe_text(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        clean = " ".join(value.split()).strip()
        key = _normalize(clean)
        if not clean or key in seen:
            continue
        seen.add(key)
        deduped.append(clean)
    return deduped


def _source_query(base_terms: str, source: dict[str, str]) -> SearchQuery | None:
    name = source.get("name") or "fuente registrada"
    domain = source.get("domain")
    handle = source.get("handle")
    platform = (source.get("platform") or "").lower()
    if domain and domain != "instagram.com":
        return SearchQuery(
            query=f"site:{domain} {base_terms}",
            relation_reason=f"Busqueda en fuente registrada: {name}",
        )
    if handle and (platform == "instagram" or domain == "instagram.com"):
        return SearchQuery(
            query=f"site:instagram.com/{handle} {base_terms}",
            relation_reason=f"Busqueda en cuenta registrada: {name}",
        )
    return None


def _dedupe_queries(queries: list[SearchQuery]) -> list[SearchQuery]:
    seen: set[str] = set()
    deduped: list[SearchQuery] = []
    for query in queries:
        key = query.query.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(query)
    return deduped


def _filter_related_items(items: list[RelatedNewsItem], seen_titles: set[str], analysis: NewsAnalysis) -> list[RelatedNewsItem]:
    filtered: list[RelatedNewsItem] = []
    for item in items:
        prepared_item = _prepare_related_item(item, analysis)
        if not prepared_item or _is_duplicate_title(item.title, seen_titles):
            continue
        if not _is_registered_related_item(item):
            continue
        seen_titles.add(_normalize(_strip_source_suffix(item.title)))
        filtered.append(prepared_item)
    return sorted(
        filtered,
        key=lambda item: (
            item.relation_score or 0,
            item.source_veracity_score or item.source_confidence_score or 0,
        ),
        reverse=True,
    )


def _prepare_related_item(item: RelatedNewsItem, analysis: NewsAnalysis) -> RelatedNewsItem | None:
    if not _is_registered_related_item(item) or not _is_related_item(item, analysis):
        return None
    relation_score = _relation_score(item, analysis)
    return item.model_copy(
        update={
            "relation_score": relation_score,
            "relation_label": _relation_label(relation_score),
        }
    )


def _is_related_item(item: RelatedNewsItem, analysis: NewsAnalysis) -> bool:
    text = f"{item.title} {item.snippet or ''}"
    result_tokens = _title_tokens(_normalize(_strip_source_suffix(text)))
    if len(result_tokens) <= 1:
        return True

    anchor_tokens = _analysis_anchor_tokens(analysis)
    if not anchor_tokens:
        return True

    if _is_electoral_analysis(analysis) and not (result_tokens & _ELECTORAL_TERMS):
        return False

    overlap = result_tokens & anchor_tokens
    if _is_electoral_analysis(analysis):
        if not _is_local_or_registered_result(item, result_tokens):
            return False
        distinctive_overlap = result_tokens & _distinctive_anchor_tokens(analysis)
        return len(overlap) >= 2 and bool(distinctive_overlap)
    if len(overlap) >= 2:
        return True
    return bool(overlap & _ELECTORAL_TERMS)


def _analysis_anchor_tokens(analysis: NewsAnalysis) -> set[str]:
    values: list[str] = []
    values.append(analysis.topic)
    values.extend(analysis.main_claims[:3])
    values.extend(analysis.keywords)
    return _title_tokens(_normalize(" ".join(value for value in values if value)))


def _distinctive_anchor_tokens(analysis: NewsAnalysis) -> set[str]:
    return {
        token
        for token in _analysis_anchor_tokens(analysis)
        if token not in _BROAD_TOPIC_TERMS and not token.isdigit()
    }


def _is_local_or_registered_result(item: RelatedNewsItem, result_tokens: set[str]) -> bool:
    if item.source_registry_status in {"radar", "registro interno"}:
        return True
    return bool(result_tokens & _ECUADOR_CONTEXT_TERMS)


def _is_registered_related_item(item: RelatedNewsItem) -> bool:
    return item.source_registry_status in {"radar", "registro interno"}


def _relation_score(item: RelatedNewsItem, analysis: NewsAnalysis) -> int:
    item_text = _normalize(_strip_source_suffix(f"{item.title} {item.snippet or ''}"))
    item_tokens = _title_tokens(item_text)
    anchor_tokens = _analysis_anchor_tokens(analysis)
    distinctive_tokens = _distinctive_anchor_tokens(analysis)
    if not item_tokens or not anchor_tokens:
        return 0

    overlap = item_tokens & anchor_tokens
    distinctive_overlap = item_tokens & distinctive_tokens
    title_similarity = len(overlap) / max(1, len(anchor_tokens))
    distinctive_bonus = min(0.25, len(distinctive_overlap) * 0.08)
    exact_topic_bonus = 0.2 if _normalize(_compact_topic_query(analysis.topic)) in item_text else 0
    score = int(round((title_similarity + distinctive_bonus + exact_topic_bonus) * 100))
    return max(20 if overlap else 0, min(100, score))


def _relation_label(score: int) -> str:
    if score >= 80:
        return "muy relacionada"
    if score >= 55:
        return "relacionada"
    if score >= 35:
        return "relacion parcial"
    return "relacion debil"


def _is_electoral_analysis(analysis: NewsAnalysis) -> bool:
    return bool(_analysis_anchor_tokens(analysis) & _ELECTORAL_TERMS)


def _is_duplicate_title(title: str | None, seen_titles: set[str]) -> bool:
    clean = _normalize(_strip_source_suffix(title or ""))
    if not clean:
        return False
    clean_tokens = _title_tokens(clean)
    for seen in seen_titles:
        if not seen:
            continue
        if clean == seen:
            return True
        if len(clean) >= 18 and len(seen) >= 18 and (clean in seen or seen in clean):
            return True
        seen_tokens = _title_tokens(seen)
        if clean_tokens and seen_tokens and len(clean_tokens & seen_tokens) / max(len(clean_tokens), len(seen_tokens)) >= 0.6:
            return True
    return False


def _title_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"\W+", value)
        if len(token) > 3 and token not in _STOPWORDS
    }


def _strip_source_suffix(title: str) -> str:
    return re.split(r"\s+-\s+", title, maxsplit=1)[0].strip()


def _extract_source_from_rss_item(title: str, item) -> str | None:
    source = item.find("source")
    if source is not None and source.text:
        return " ".join(source.text.split()).strip()
    parts = re.split(r"\s+-\s+", title)
    if len(parts) > 1:
        return parts[-1].strip()
    return None


def _find_registered_source_by_name(source_label: str | None) -> dict[str, str] | None:
    if not source_label:
        return None
    normalized_label = _normalize(source_label)
    normalized_domain_label = normalized_label.removeprefix("www.")
    for source in list_registered_sources_for_search(None):
        source_name = _normalize(source.get("name") or "")
        source_domain = _normalize((source.get("domain") or "").removeprefix("www."))
        if source_name and (normalized_label == source_name or normalized_label in source_name or source_name in normalized_label):
            return source
        if source_domain and normalized_domain_label == source_domain:
            return source
    return None


def _search_public_web(query: str, relation_reason: str) -> list[RelatedNewsItem]:
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
        with urlopen(request, timeout=settings.duckduckgo_timeout_seconds) as response:
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
        results.append(_build_related_item(raw_title, url, snippet, relation_reason))
    return results


def _build_related_item(
    title: str,
    url: str,
    snippet: str | None,
    relation_reason: str,
    published_at: str | None = None,
    source_domain: str | None = None,
) -> RelatedNewsItem:
    parsed = urlparse(url)
    domain = (source_domain or parsed.netloc).lower()
    source_classification = classify_source(url, domain)
    source_veracity_score = _source_veracity_score(source_classification)
    return RelatedNewsItem(
        title=title or "Sin titulo",
        url=url,
        source=domain or None,
        source_name=source_classification.source_name,
        source_type=source_classification.communication_type,
        source_registry_status=_source_registry_status(source_classification),
        source_confidence_score=round(source_classification.confidence * 100),
        source_veracity_score=source_veracity_score,
        snippet=snippet,
        published_at=published_at,
        relation_reason=relation_reason,
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


def _source_veracity_score(source_classification) -> int:
    if source_classification.verification_network:
        return 98
    if source_classification.is_radar_media:
        return 95
    if source_classification.source_name:
        return 90
    if source_classification.communication_type in {"medio_no_radar", "gobierno", "institucion"}:
        return 70
    return round(source_classification.confidence * 100)


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
