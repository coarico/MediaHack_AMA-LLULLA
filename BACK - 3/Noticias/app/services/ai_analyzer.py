from app.core.config import settings
from app.schemas.news import (
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
    EntitySet,
    ExtractedArticle,
    InformationGap,
    NewsAnalysis,
    SentimentAnalysis,
)
from app.services.keyword_extractor import extract_keywords, infer_category_from_keywords, merge_keywords


ANALYSIS_SCHEMA = {
    "name": "news_analysis",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "topic": {"type": "string"},
            "category": {"type": "string"},
            "main_claims": {"type": "array", "items": {"type": "string"}},
            "entities": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "people": {"type": "array", "items": {"type": "string"}},
                    "organizations": {"type": "array", "items": {"type": "string"}},
                    "locations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["people", "organizations", "locations"],
            },
            "keywords": {"type": "array", "items": {"type": "string"}},
            "search_queries": {"type": "array", "items": {"type": "string"}},
            "sentiment": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "label": {"type": "string", "enum": ["positivo", "neutral", "negativo", "mixto"]},
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["label", "score"],
            },
            "bias_analysis": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "direction": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["score", "direction", "explanation"],
            },
            "manipulation_signals": {"type": "array", "items": {"type": "string"}},
            "clickbait": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["score", "evidence"],
            },
            "credibility": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "risk_level": {"type": "string", "enum": ["bajo", "medio", "alto", "critico"]},
                    "explanation": {"type": "string"},
                },
                "required": ["score", "risk_level", "explanation"],
            },
            "information_gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "missing_item": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "suggested_verification": {"type": "string"},
                        "priority": {"type": "string", "enum": ["baja", "media", "alta"]},
                    },
                    "required": [
                        "missing_item",
                        "why_it_matters",
                        "suggested_verification",
                        "priority",
                    ],
                },
            },
            "missing_context": {"type": "array", "items": {"type": "string"}},
            "recommendation": {"type": "string"},
        },
        "required": [
            "summary",
            "topic",
            "category",
            "main_claims",
            "entities",
            "keywords",
            "search_queries",
            "sentiment",
            "bias_analysis",
            "manipulation_signals",
            "clickbait",
            "credibility",
            "information_gaps",
            "missing_context",
            "recommendation",
        ],
    },
    "strict": True,
}


async def analyze_article(article: ExtractedArticle) -> NewsAnalysis:
    if not settings.openai_api_key:
        return _heuristic_analysis(article)

    import json
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "Eres un analista periodistico y de desinformacion electoral. "
                    "Evalua calidad informativa, sesgo, manipulacion, clickbait, contexto faltante "
                    "y confiabilidad. Identifica con precision que informacion falta en la noticia: "
                    "datos, fuentes, cifras, fechas, documentos, contexto historico, versiones de actores "
                    "afectados o evidencia primaria. No afirmes que algo es falso sin evidencia externa; "
                    "habla de riesgo."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"URL: {article.url}\n"
                    f"Fuente: {article.source_domain}\n"
                    f"Titulo: {article.title or 'Sin titulo'}\n\n"
                    f"Texto:\n{article.text}"
                ),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": ANALYSIS_SCHEMA["name"],
                "schema": ANALYSIS_SCHEMA["schema"],
                "strict": True,
            }
        },
    )
    payload = json.loads(response.output_text)
    analysis = NewsAnalysis.model_validate(payload)
    title_keywords = extract_keywords(article)
    analysis.keywords = merge_keywords(title_keywords, analysis.keywords)
    analysis.category = infer_category_from_keywords(analysis.keywords, analysis.category)
    analysis.search_queries = _build_search_queries(article.title or analysis.topic, analysis.keywords)
    return analysis


def _heuristic_analysis(article: ExtractedArticle) -> NewsAnalysis:
    title = article.title or "Noticia sin titulo"
    keywords = extract_keywords(article)
    summary = article.text[:600].strip()
    if len(article.text) > 600:
        summary += "..."

    risk_words = ["urgente", "escandalo", "impactante", "secreto", "fraude", "corrupcion"]
    risk_hits = [word for word in risk_words if word in article.text.lower() or word in title.lower()]
    risk_score = min(70, 20 + len(risk_hits) * 10)

    return NewsAnalysis(
        summary=summary,
        topic=title,
        category=infer_category_from_keywords(keywords),
        main_claims=[title],
        entities=EntitySet(),
        keywords=keywords,
        search_queries=_build_search_queries(title, keywords),
        sentiment=SentimentAnalysis(label="neutral", score=0.5),
        bias_analysis=BiasAnalysis(
            score=30,
            direction="no determinado",
            explanation="Analisis local sin modelo IA; requiere OPENAI_API_KEY para evaluacion profunda.",
        ),
        manipulation_signals=risk_hits,
        clickbait=ClickbaitAnalysis(score=min(100, len(risk_hits) * 20), evidence=risk_hits),
        credibility=CredibilityAnalysis(
            score=max(0, 100 - risk_score),
            risk_level="medio" if risk_hits else "bajo",
            explanation="Puntaje heuristico local. Activar OpenAI para analisis argumentado.",
        ),
        information_gaps=[
            InformationGap(
                missing_item="Fuentes independientes o evidencia primaria",
                why_it_matters="Sin contrastar con documentos, autoridades o medios adicionales no se puede validar la afirmacion central.",
                suggested_verification="Buscar documentos oficiales, declaraciones completas y cobertura de otros medios sobre el mismo hecho.",
                priority="alta",
            )
        ],
        missing_context=["Contrastar con fuentes independientes y documentos oficiales."],
        recommendation="Usar este resultado como vista previa local; configurar OpenAI para analisis fuerte.",
    )


def _build_search_queries(title: str, keywords: list[str]) -> list[str]:
    base_title = title.strip()
    compact_keywords = " ".join(keywords[:5])
    queries = [
        f"{base_title} {compact_keywords}".strip(),
        compact_keywords.strip(),
    ]
    return [query for index, query in enumerate(queries) if query and query not in queries[:index]]
