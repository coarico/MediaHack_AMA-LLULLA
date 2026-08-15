import asyncio
from types import SimpleNamespace

from app.schemas.news import (
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
    EntitySet,
    NewsAnalysis,
    SentimentAnalysis,
)
from app.services import related_search


def test_build_related_search_queries_uses_general_then_registered_domains(monkeypatch) -> None:
    monkeypatch.setattr(related_search, "settings", SimpleNamespace(related_source_search_limit=3))
    monkeypatch.setattr(
        related_search,
        "list_registered_sources_for_search",
        lambda limit: [
            {"name": "Ecuador Chequea", "domain": "ecuadorchequea.com", "handle": None, "platform": "sitio_web"},
            {"name": "El Comercio", "domain": "elcomercio.com", "handle": None, "platform": "sitio_web"},
            {"name": "Radio Centro", "domain": "instagram.com", "handle": "radiocentro.ec", "platform": "instagram"},
        ][:limit],
    )

    queries = related_search.build_related_search_queries(_analysis())

    assert queries[0].relation_reason.startswith("Busqueda general GDELT")
    assert any(query.query.startswith("site:ecuadorchequea.com ") for query in queries)
    assert any(query.query.startswith("site:elcomercio.com ") for query in queries)
    assert any(query.query.startswith("site:instagram.com/radiocentro.ec ") for query in queries)


def test_gdelt_query_transforms_site_domain_operator() -> None:
    query = related_search._to_gdelt_query("site:elcomercio.com inseguridad Quito")

    assert query == "domainis:elcomercio.com inseguridad Quito"


def test_gdelt_query_transforms_instagram_handle_operator() -> None:
    query = related_search._to_gdelt_query("site:instagram.com/radiocentro.ec ministro entrevista")

    assert query == "domainis:instagram.com radiocentro.ec ministro entrevista"


def test_build_gdelt_item_keeps_source_metadata() -> None:
    item = related_search._build_gdelt_item(
        {
            "title": "Titulo relacionado",
            "url": "https://www.elcomercio.com/noticia",
            "domain": "elcomercio.com",
            "seendate": "20260814T120000Z",
        },
        "Busqueda en fuente registrada: El Comercio",
    )

    assert item.source_name == "El Comercio"
    assert item.source_registry_status == "radar"
    assert item.relation_reason.startswith("GDELT gratuito")
    assert item.published_at == "20260814T120000Z"


def test_search_related_news_uses_gdelt_then_public_fallback(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        related_search,
        "settings",
        SimpleNamespace(
            related_source_search_limit=0,
            related_news_limit=2,
            gdelt_enabled=True,
            gdelt_query_limit=1,
            gdelt_timespan="3months",
            gdelt_max_records=2,
            news_rss_enabled=False,
            news_rss_query_limit=0,
            news_rss_timeout_seconds=1,
            duckduckgo_fallback_query_limit=2,
        ),
    )
    monkeypatch.setattr(
        related_search,
        "_search_gdelt_queries",
        lambda queries, seen_urls: _async_return([]),
    )

    def fake_public(query, relation_reason):
        calls.append((query, relation_reason))
        return []

    monkeypatch.setattr(related_search, "_search_public_web", fake_public)

    asyncio.run(related_search.search_related_news(_analysis(), "https://example.com/original"))

    assert calls
    assert not calls[0][0].startswith("site:")


def test_public_related_queries_are_built_from_inserted_news() -> None:
    queries = related_search.build_public_related_queries(
        _analysis(),
        [
            related_search.SearchQuery(
                query="site:elcomercio.com Inseguridad en la Simon Bolivar preocupa a Quito",
                relation_reason="Busqueda en fuente registrada: El Comercio",
            )
        ],
    )

    assert queries[0].relation_reason.startswith("Consulta relacionada con la noticia ingresada")
    assert queries[0].query == '"Simon Bolivar" Quito'
    assert any(query.query == "inseguridad Quito" for query in queries)
    assert queries[-1].query.startswith("site:elcomercio.com ")


def test_electoral_related_queries_ignore_weak_keyword() -> None:
    queries = related_search.build_public_related_queries(_electoral_analysis(), [])

    assert queries[0].query == "postulaciones acuerdos politicos elecciones 2027"
    assert "via publica" not in " ".join(query.query.lower() for query in queries[:3])


def test_electoral_related_filter_rejects_unrelated_public_road_result() -> None:
    unrelated = related_search.RelatedNewsItem(
        title="Hallan a una mujer muerta en plena via publica en Vallejo - Telemundo",
        url="https://example.com/unrelated",
    )
    related = related_search.RelatedNewsItem(
        title="Partidos avanzan en acuerdos politicos para las elecciones 2027 - Primicias",
        url="https://example.com/related",
        source_registry_status="registro interno",
    )

    assert not related_search._is_related_item(unrelated, _electoral_analysis())
    assert related_search._is_related_item(related, _electoral_analysis())


def test_electoral_related_filter_rejects_foreign_generic_election_result() -> None:
    foreign = related_search.RelatedNewsItem(
        title="Elecciones 2027: Los perfiles que podrian unir al PRI y al PAN - Marquesina Politica",
        url="https://example.com/foreign",
        source_registry_status="sin registro",
    )
    local_registered = related_search.RelatedNewsItem(
        title="CNE y Contraloria controlaran uso de bienes en Elecciones 2027 - El Comercio",
        url="https://example.com/local",
        source_registry_status="registro interno",
    )
    same_context_registered = related_search.RelatedNewsItem(
        title="Postulaciones y acuerdos politicos avanzan para las elecciones de 2027 - Primicias",
        url="https://example.com/same-context",
        source_registry_status="registro interno",
    )

    assert not related_search._is_related_item(foreign, _electoral_analysis())
    assert not related_search._is_related_item(local_registered, _electoral_analysis())
    assert related_search._is_related_item(same_context_registered, _electoral_analysis())


def test_iter_related_news_batches_yields_partial_batches(monkeypatch) -> None:
    monkeypatch.setattr(
        related_search,
        "settings",
        SimpleNamespace(
            related_source_search_limit=0,
            related_news_limit=4,
            gdelt_enabled=True,
            gdelt_query_limit=1,
            gdelt_timespan="3months",
            gdelt_max_records=4,
            news_rss_enabled=False,
            news_rss_query_limit=0,
            news_rss_timeout_seconds=1,
            duckduckgo_fallback_query_limit=0,
        ),
    )
    monkeypatch.setattr(
        related_search,
        "_fetch_gdelt",
        lambda query: {
            "articles": [
                {
                    "title": "Inseguridad en la Simon Bolivar preocupa a Quito - Primicias",
                    "url": "https://www.primicias.ec/1",
                    "domain": "primicias.ec",
                },
                {
                    "title": "Hechos violentos recientes en la avenida Simon Bolivar de Quito - El Universo",
                    "url": "https://www.eluniverso.com/2",
                    "domain": "eluniverso.com",
                },
                {
                    "title": "Seguridad vial e inseguridad en Quito: nuevos operativos - Ecuavisa",
                    "url": "https://www.ecuavisa.com/3",
                    "domain": "ecuavisa.com",
                },
            ]
        },
    )

    async def collect():
        batches = []
        async for batch in related_search.iter_related_news_batches(_analysis(), "https://original.com", min_batch_size=2):
            batches.append(batch)
        return batches

    batches = asyncio.run(collect())

    assert [len(batch) for batch in batches] == [1, 1]
    assert all(item.source_registry_status == "radar" for batch in batches for item in batch)
    assert all(item.relation_score is not None for batch in batches for item in batch)
    assert all(item.source_veracity_score is not None for batch in batches for item in batch)


def test_news_rss_items_use_registered_source_from_title(monkeypatch) -> None:
    monkeypatch.setattr(
        related_search,
        "settings",
        SimpleNamespace(related_news_limit=3, news_rss_timeout_seconds=1),
    )
    monkeypatch.setattr(
        related_search,
        "list_registered_sources_for_search",
        lambda limit: [
            {"name": "El Universo", "domain": "eluniverso.com", "handle": None, "platform": "sitio_web"},
        ],
    )

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b"""<?xml version="1.0" encoding="UTF-8" ?>
            <rss><channel><item>
            <title>Cuerpo sin vida fue encontrado en la av. Simon Bolivar en Quito - El Universo</title>
            <link>https://news.google.com/rss/articles/test</link>
            <pubDate>Fri, 14 Aug 2026 12:00:00 GMT</pubDate>
            </item></channel></rss>"""

    monkeypatch.setattr(related_search, "urlopen", lambda request, timeout: FakeResponse())

    items = related_search._search_news_rss("Simon Bolivar Quito", "Consulta relacionada")

    assert len(items) == 1
    assert items[0].source_name == "El Universo"
    assert items[0].source_registry_status == "radar"


async def _async_return(value):
    return value


def _analysis() -> NewsAnalysis:
    return NewsAnalysis(
        summary="Resumen",
        topic="Inseguridad en la Simon Bolivar preocupa a Quito",
        category="noticias",
        main_claims=["La avenida Simon Bolivar registro hechos violentos recientes."],
        entities=EntitySet(),
        keywords=["inseguridad", "Simon Bolivar", "Quito", "seguridad vial"],
        search_queries=["Inseguridad Simon Bolivar Quito"],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=0, direction="neutral", explanation="Test"),
        manipulation_signals=[],
        clickbait=ClickbaitAnalysis(score=0, evidence=[]),
        credibility=CredibilityAnalysis(score=80, risk_level="bajo", explanation="Test"),
        information_gaps=[],
        missing_context=[],
        recommendation="Contrastar.",
    )


def _electoral_analysis() -> NewsAnalysis:
    return NewsAnalysis(
        summary="Resumen",
        topic="Avanzan las postulaciones y acuerdos politicos para las elecciones 2027",
        category="politica",
        main_claims=["Organizaciones politicas preparan postulaciones y acuerdos para las elecciones de 2027."],
        entities=EntitySet(),
        keywords=[
            "elecciones",
            "2027",
            "Avanzan",
            "acuerdos",
            "politicos",
            "postulaciones",
            "via publica",
            "Comercio",
            "Electoral",
            "postulantes",
        ],
        search_queries=["postulaciones acuerdos politicos elecciones 2027"],
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(score=0, direction="neutral", explanation="Test"),
        manipulation_signals=[],
        clickbait=ClickbaitAnalysis(score=0, evidence=[]),
        credibility=CredibilityAnalysis(score=88, risk_level="bajo", explanation="Test"),
        information_gaps=[],
        missing_context=[],
        recommendation="Contrastar.",
    )
