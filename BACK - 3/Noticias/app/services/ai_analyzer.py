from app.core.config import settings
from app.schemas.news import (
    BiasAnalysis,
    ClickbaitAnalysis,
    CredibilityAnalysis,
    EntitySet,
    ExtractedArticle,
    InformationGap,
    LlmCompactContext,
    LlmExecutionMetadata,
    NewsAnalysis,
    SentimentAnalysis,
)
from app.services.keyword_extractor import extract_keywords, infer_category_from_keywords, merge_keywords
from app.services.llm_context import build_llm_compact_context, compact_context_to_prompt


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


async def analyze_article(article: ExtractedArticle, compact_context: LlmCompactContext | None = None) -> NewsAnalysis:
    analysis, _ = await analyze_article_with_metadata(article, compact_context)
    return analysis


async def analyze_article_with_metadata(
    article: ExtractedArticle,
    compact_context: LlmCompactContext | None = None,
) -> tuple[NewsAnalysis, LlmExecutionMetadata]:
    compact_context = compact_context or build_llm_compact_context(article)
    provider = _resolve_provider(strict=True)
    if provider is None:
        return _heuristic_analysis(article, compact_context), LlmExecutionMetadata(
            provider="heuristic",
            model=None,
            status="disabled",
            error=None,
        )

    try:
        if provider == "groq":
            analysis = await _analyze_with_groq(article, compact_context)
            return analysis, LlmExecutionMetadata(provider="groq", model=settings.groq_model, status="used")
        analysis = await _analyze_with_openai(article, compact_context)
        return analysis, LlmExecutionMetadata(provider="openai", model=settings.openai_model, status="used")
    except Exception as exc:
        if not settings.llm_fallback_on_error:
            raise
        fallback = _heuristic_analysis(article, compact_context)
        fallback.missing_context.append(f"LLM no disponible: {exc}")
        fallback.recommendation = (
            "Analisis local generado porque el proveedor LLM fallo. "
            "Revisa GROQ_API_KEY, GROQ_MODEL y permisos de la cuenta."
        )
        return fallback, LlmExecutionMetadata(
            provider=provider,
            model=settings.groq_model if provider == "groq" else settings.openai_model,
            status="fallback",
            error=str(exc),
        )


async def _analyze_with_openai(article: ExtractedArticle, compact_context: LlmCompactContext) -> NewsAnalysis:
    if not settings.openai_api_key:
        return _heuristic_analysis(article, compact_context)

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
                "habla de riesgo. Recibiras un contexto compacto generado por Python; no inventes "
                "datos que no esten en ese contexto. En search_queries devuelve 3 a 5 consultas "
                "especificas para encontrar cobertura relacionada del mismo hecho/contexto, no del "
                "tema general. Incluye terminos distintivos del titulo, entidades y ubicacion."
            ),
            },
            {
                "role": "user",
                "content": (
                    "Analiza esta noticia usando solo el contexto compacto. "
                    "Devuelve JSON estricto con el esquema solicitado.\n\n"
                    f"{compact_context_to_prompt(compact_context)}"
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
    analysis = NewsAnalysis.model_validate(_coerce_analysis_payload(payload))
    return _finalize_analysis(article, analysis)


async def _analyze_with_groq(article: ExtractedArticle, compact_context: LlmCompactContext) -> NewsAnalysis:
    if not settings.groq_api_key:
        return _heuristic_analysis(article, compact_context)

    import asyncio
    import json

    payload = _build_groq_payload(compact_context)
    response_payload = await asyncio.to_thread(_post_groq_completion, payload)

    content = response_payload.get("choices", [{}])[0].get("message", {}).get("content") or "{}"
    payload = json.loads(content)
    analysis = NewsAnalysis.model_validate(_coerce_analysis_payload(payload))
    return _finalize_analysis(article, analysis)


def _coerce_analysis_payload(payload: dict) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    payload.setdefault("summary", "")
    payload.setdefault("topic", "")
    payload.setdefault("category", "noticias")
    payload["main_claims"] = _coerce_string_list(payload.get("main_claims"))
    payload["keywords"] = _coerce_string_list(payload.get("keywords"))
    payload["search_queries"] = _coerce_string_list(payload.get("search_queries"))
    payload["missing_context"] = _coerce_string_list(payload.get("missing_context"))
    payload["recommendation"] = str(payload.get("recommendation") or "Contrastar con evidencia adicional.")

    entities = payload.get("entities")
    if not isinstance(entities, dict):
        entities = {}
    payload["entities"] = {
        "people": _coerce_string_list(entities.get("people")),
        "organizations": _coerce_string_list(entities.get("organizations")),
        "locations": _coerce_string_list(entities.get("locations")),
    }

    sentiment = payload.get("sentiment")
    if isinstance(sentiment, str):
        sentiment = {"label": sentiment}
    if not isinstance(sentiment, dict):
        sentiment = {}
    sentiment_label = str(sentiment.get("label") or "neutral").lower()
    if sentiment_label not in {"positivo", "neutral", "negativo", "mixto"}:
        sentiment_label = "neutral"
    payload["sentiment"] = {
        "label": sentiment_label,
        "score": _bounded_float(sentiment.get("score"), 0, 1, 0.5),
    }

    bias = payload.get("bias_analysis")
    if isinstance(bias, str):
        bias = {"explanation": bias}
    if not isinstance(bias, dict):
        bias = {}
    payload["bias_analysis"] = {
        "score": _bounded_int(bias.get("score"), 0, 100, 20),
        "direction": str(bias.get("direction") or bias.get("tone") or "no determinado"),
        "explanation": str(bias.get("explanation") or "El modelo no entrego una explicacion detallada del sesgo."),
    }

    signals = payload.get("manipulation_signals")
    if isinstance(signals, dict):
        signals = [key for key, value in signals.items() if value]
    payload["manipulation_signals"] = _coerce_string_list(signals)

    clickbait = payload.get("clickbait")
    if isinstance(clickbait, bool):
        clickbait = {"score": 40 if clickbait else 0, "evidence": []}
    if isinstance(clickbait, str):
        clickbait = {"score": 30, "evidence": [clickbait]}
    if not isinstance(clickbait, dict):
        clickbait = {}
    payload["clickbait"] = {
        "score": _bounded_int(clickbait.get("score"), 0, 100, 0),
        "evidence": _coerce_string_list(clickbait.get("evidence")),
    }

    credibility = payload.get("credibility")
    if isinstance(credibility, int | float):
        credibility = {"score": credibility}
    if not isinstance(credibility, dict):
        credibility = {}
    risk_level = str(credibility.get("risk_level") or "medio").lower()
    if risk_level not in {"bajo", "medio", "alto", "critico"}:
        risk_level = "medio"
    payload["credibility"] = {
        "score": _bounded_int(credibility.get("score"), 0, 100, 70),
        "risk_level": risk_level,
        "explanation": str(credibility.get("explanation") or "Evaluacion generada por LLM con normalizacion de esquema."),
    }

    payload["information_gaps"] = _coerce_information_gaps(payload.get("information_gaps"))
    return payload


def _coerce_information_gaps(value) -> list[dict]:
    if not isinstance(value, list):
        value = [value] if value else []
    gaps = []
    for item in value:
        if isinstance(item, str):
            item = {"missing_item": item}
        if not isinstance(item, dict):
            continue
        priority = str(item.get("priority") or "media").lower()
        if priority not in {"baja", "media", "alta"}:
            priority = "media"
        gaps.append(
            {
                "missing_item": str(item.get("missing_item") or item.get("label") or "Informacion faltante"),
                "why_it_matters": str(item.get("why_it_matters") or item.get("reason") or "Ayuda a contextualizar la informacion antes de auditoria."),
                "suggested_verification": str(item.get("suggested_verification") or item.get("recommendation") or "Contrastar con fuentes independientes y evidencia primaria."),
                "priority": priority,
            }
        )
    return gaps[:5]


def _coerce_string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, dict):
        return [str(key) for key, item_value in value.items() if item_value]
    if not isinstance(value, list):
        return [str(value)]
    return [str(item).strip() for item in value if str(item).strip()]


def _bounded_int(value, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _bounded_float(value, minimum: float, maximum: float, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _build_groq_payload(compact_context: LlmCompactContext) -> dict:
    return {
        "model": settings.groq_model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un analista periodistico y de desinformacion electoral. "
                    "Usa solo el contexto compacto entregado por Python. No concluyas verdad o fraude. "
                    "Devuelve exclusivamente JSON valido con estas claves obligatorias: "
                    "summary, topic, category, main_claims, entities, keywords, search_queries, sentiment, "
                    "bias_analysis, manipulation_signals, clickbait, credibility, information_gaps, "
                    "missing_context, recommendation. entities debe contener people, organizations y locations. "
                    "sentiment.label debe ser positivo, neutral, negativo o mixto. "
                    "credibility.risk_level debe ser bajo, medio, alto o critico. "
                    "En search_queries devuelve 3 a 5 consultas especificas para buscar noticias "
                    "relacionadas con el mismo hecho o contexto de la URL insertada. No uses "
                    "consultas genericas como solo 'elecciones 2027' si el titulo contiene "
                    "terminos mas concretos."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analiza esta noticia usando solo el contexto compacto. "
                    "Responde en JSON estricto compatible con el esquema solicitado.\n\n"
                    f"{compact_context_to_prompt(compact_context)}"
                ),
            },
        ],
    }


def _post_groq_completion(payload: dict) -> dict:
    import json
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    request = Request(
        f"{settings.groq_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AMA-LLU-IA/0.1 Python/3.11",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.request_timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(_format_groq_http_error(exc.code, detail)) from exc
    except URLError as exc:
        raise RuntimeError(f"Error conectando con Groq: {exc.reason}") from exc


def _format_groq_http_error(status_code: int, detail: str) -> str:
    clean_detail = " ".join((detail or "").split())
    if status_code == 401:
        return "Groq rechazo la API key. Genera una key nueva en Groq Console y reinicia el backend."
    if status_code == 403:
        return (
            "Groq rechazo la solicitud con HTTP 403. Si tambien falla /models, no es problema del prompt: "
            "revisa que la API key pertenezca a Groq Console, que el proyecto tenga acceso API activo, "
            "que la key no este revocada y que la red/IP no este bloqueada por Groq."
        )
    if status_code == 404:
        return f"Groq no encontro el modelo configurado ({settings.groq_model}). Revisa GROQ_MODEL."
    if status_code == 429:
        return "Groq limito la solicitud por cuota o rate limit. Espera o usa un modelo mas liviano."
    return f"Error Groq HTTP {status_code}: {clean_detail[:500]}"


def _finalize_analysis(article: ExtractedArticle, analysis: NewsAnalysis) -> NewsAnalysis:
    title_keywords = extract_keywords(article)
    analysis.keywords = merge_keywords(title_keywords, analysis.keywords)
    analysis.category = infer_category_from_keywords(analysis.keywords, analysis.category)
    analysis.search_queries = _merge_search_queries(
        analysis.search_queries,
        _build_search_queries(article.title or analysis.topic, analysis.keywords),
    )
    return analysis


def _merge_search_queries(llm_queries: list[str], fallback_queries: list[str], limit: int = 6) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for query in [*llm_queries, *fallback_queries]:
        clean = _clean_search_query(query)
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(clean)
        if len(merged) >= limit:
            break
    return merged


def _clean_search_query(query: str) -> str:
    import re

    clean = re.sub(r"\s+", " ", (query or "").strip())
    weak_queries = {"via publica", "elecciones", "elecciones 2027", "noticias", "politica"}
    if clean.lower() in weak_queries:
        return ""
    return clean[:180]


def _resolve_provider(strict: bool = False) -> str | None:
    provider = (settings.llm_provider or "auto").lower()
    if provider == "groq":
        if settings.groq_api_key:
            return "groq"
        if strict:
            raise RuntimeError("LLM_PROVIDER=groq requiere GROQ_API_KEY en variables de entorno.")
        return None
    if provider == "openai":
        if settings.openai_api_key:
            return "openai"
        if strict:
            raise RuntimeError("LLM_PROVIDER=openai requiere OPENAI_API_KEY en variables de entorno.")
        return None
    if provider == "none":
        return None
    if settings.groq_api_key:
        return "groq"
    if settings.openai_api_key:
        return "openai"
    return None


def _heuristic_analysis(article: ExtractedArticle, compact_context: LlmCompactContext | None = None) -> NewsAnalysis:
    compact_context = compact_context or build_llm_compact_context(article)
    title = article.title or "Noticia sin titulo"
    keywords = compact_context.keywords or extract_keywords(article)
    summary = " ".join(compact_context.top_sentences[:3]).strip() or article.text[:600].strip()
    if len(summary) > 600:
        summary = summary[:600].strip()
    if len(article.text) > 600 and not summary.endswith("..."):
        summary += "..."

    risk_words = ["urgente", "escandalo", "impactante", "secreto", "fraude", "corrupcion"]
    risk_hits = [word for word in risk_words if word in article.text.lower() or word in title.lower()]
    risk_score = min(70, 20 + len(risk_hits) * 10)

    return NewsAnalysis(
        summary=summary,
        topic=title,
        category=infer_category_from_keywords(keywords),
        main_claims=compact_context.candidate_claims[:5] or [title],
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
