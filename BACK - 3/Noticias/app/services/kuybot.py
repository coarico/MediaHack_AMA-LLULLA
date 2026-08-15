from __future__ import annotations

import json
from urllib.parse import urlparse
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.news import KuybotFactCheckItem, KuybotResponse


SYSTEM_PROMPT = """Eres Kuybot, asistente de investigación y verificación periodística de AMA LLU IA.

Tu función es ayudar al usuario a investigar una noticia previamente analizada por la plataforma.
No eres una fuente de verdad. Tu labor es contrastar contextos, afirmaciones y fuentes.
Prioriza las fuentes según la jerarquía editorial como contexto y prioridad, no como verdad absoluta.
Diferencia entre hechos, afirmaciones, opiniones, interpretaciones, evidencia y ausencia de evidencia.
Cuando exista información oficial, priorízala.
Cuando haya contradicciones, muéstralas.
Cuando no haya pruebas suficientes, dilo de forma clara.
Nunca inventes fuentes, URLs, citas o fechas.
Tu respuesta debe ser breve, clara y explicada, con un formato útil para reportar investigación periodística.
Devuelve una conclusión, por qué se concluye así, evidencia y fuentes.
"""


def _infer_question_intent(question: str) -> str:
    q = (question or "").lower()

    if any(term in q for term in ["es verdad", "verdad", "falso", "mentira", "confirmado", "desmentido", "verificado"]):
        return "verification"
    if any(term in q for term in ["fuente oficial", "qué dijo", "dice el cne", "dice la fiscalía", "fuentes oficiales", "institución", "ministerio"]):
        return "official_source"
    if any(term in q for term in ["contrad", "contrario", "opuesto", "coincide", "compare", "compar", "diferencia"]):
        return "contrast"
    if any(term in q for term in ["fuente", "respald", "apoyan", "qué fuentes", "documentan", "evidencia"]):
        return "sources"
    if any(term in q for term in ["antecedente", "historia", "pasado", "anteriormente", "relacionado", "noticias relacionadas"]):
        return "background"
    if any(term in q for term in ["qué pasó", "qué ocurrió", "qué sucedió", "contexto"]):
        return "context"
    return "general"


async def ask_kuybot(question: str, news: dict | None, history: list[dict] | None = None) -> KuybotResponse:
    payload = _build_context(news, question, history or [])
    intent = _infer_question_intent(question)
    payload["intent"] = intent

    fact_check = await _search_fact_checks(payload.get("question"), payload.get("news", {}).get("title"), payload.get("news", {}).get("main_claims", []))
    search_results = await _search_web_results(payload)
    payload["evidence"] = {
        "fact_checks": [item.model_dump(exclude_none=True) for item in fact_check],
        "search_results": search_results,
        "official_sources": _extract_official_sources(payload),
        "intent": intent,
    }

    if settings.gemini_api_key:
        try:
            return await _ask_gemini(payload, fact_check, search_results)
        except Exception:
            pass

    return _fallback_response(payload, fact_check, search_results)


def _build_context(news: dict | None, question: str, history: list[dict]) -> dict:
    info = news or {}
    article = info.get("article") or {}
    analysis = info.get("analysis") or {}
    audit = info.get("audit") or {}
    related_news = info.get("related_news") or []
    verifiable_claims = info.get("verifiable_claims") or []

    return {
        "question": question,
        "news": {
            "title": article.get("title"),
            "url": article.get("url") or info.get("source_input", {}).get("original_url"),
            "summary": analysis.get("summary"),
            "main_claims": analysis.get("main_claims", []),
            "keywords": analysis.get("keywords", []),
            "risk_level": info.get("risk_assessment", {}).get("level"),
            "audit_summary": audit.get("evidence_summary"),
            "related_news": [
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "source": item.get("source_name") or item.get("source"),
                    "source_type": item.get("source_type"),
                    "snippet": item.get("snippet"),
                }
                for item in related_news[:10]
            ],
            "claims": [
                {"claim": item.get("claim"), "type": item.get("type")} for item in verifiable_claims[:5]
            ],
        },
        "history": history,
    }


async def _ask_gemini(payload: dict, fact_check: list[KuybotFactCheckItem], search_results: list[dict]) -> KuybotResponse:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    model_name = settings.gemini_model or "gemini-3.5-flash"
    prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    full_prompt = SYSTEM_PROMPT + "\n\nINFORMACION CONTEXTUAL:\n" + prompt

    response = client.models.generate_content(model=model_name, contents=full_prompt)
    answer = getattr(response, "text", None) or (
        response.candidates[0].content.parts[0].text if getattr(response, "candidates", None) else "No se pudo obtener respuesta del modelo."
    )

    sources = _unique_urls(
        [item.get("url") for item in search_results if item.get("url")] +
        [item.url for item in fact_check if item.url] +
        [item.get("url") for item in (payload.get("news", {}).get("related_news") or []) if item.get("url")]
    )

    return KuybotResponse(
        answer=answer,
        sources=sources[:10],
        fact_check=fact_check,
        mode="gemini",
        status="ok",
    )


async def _search_fact_checks(question: str, title: str | None, claims: list[str]) -> list[KuybotFactCheckItem]:
    if not settings.fact_check_api_key:
        return []

    query = question or title or " ".join(claims[:2])
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"key": settings.fact_check_api_key, "query": query, "maxAgeDays": 3650}

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                return []
            payload = response.json()
            items = payload.get("claims") or []
            facts: list[KuybotFactCheckItem] = []
            for item in items[:3]:
                facts.append(
                    KuybotFactCheckItem(
                        text=(item.get("text" ) or {}).get("text"),
                        claimant=(item.get("claimant") or {}).get("name"),
                        publisher=(item.get("publisher") or {}).get("name"),
                        review_date=item.get("reviewDate"),
                        url=(item.get("url") or {}).get("url"),
                        language_code=item.get("languageCode"),
                    )
                )
            return facts
    except Exception:
        return []


async def _search_web_results(payload: dict) -> list[dict]:
    if not settings.google_search_api_key or not settings.google_search_cx:
        return []

    query = payload.get("question") or payload.get("news", {}).get("title") or " ".join((payload.get("news", {}) or {}).get("main_claims", [])[:2])
    if not query:
        return []

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.google_search_api_key,
                    "cx": settings.google_search_cx,
                    "q": query,
                    "num": 4,
                },
            )
            if response.status_code != 200:
                return []
            items = response.json().get("items") or []
            return [
                {
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": item.get("displayLink"),
                }
                for item in items[:4]
            ]
    except Exception:
        return []


def _extract_official_sources(payload: dict) -> list[dict]:
    related = payload.get("news", {}).get("related_news") or []
    priorities = {
        "gobierno": 0,
        "institucion": 1,
        "ministerio": 1,
        "presidencia": 1,
        "fiscalia": 1,
        "medio_radar": 2,
        "medio_verificacion": 2,
        "medio_no_radar": 3,
        "medio_nativo": 4,
        "cuenta_digital": 5,
    }

    ranked: list[tuple[int, dict]] = []
    for item in related:
        source_type = (item.get("source_type") or "").lower()
        if not source_type:
            continue
        source_name = item.get("source") or item.get("source_name") or "Fuente relacionada"
        ranked.append((priorities.get(source_type, 99), {
            "title": item.get("title"),
            "url": item.get("url"),
            "source": source_name,
            "source_type": item.get("source_type"),
        }))

    ranked.sort(key=lambda row: row[0])
    official = [item for _, item in ranked][:5]
    return official


def _unique_urls(urls: list[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def _format_source_links(urls: list[str]) -> str:
    if not urls:
        return 'Sin fuentes disponibles.'
    items: list[str] = []
    for url in urls[:5]:
        host = urlparse(url).netloc or url
        host = host.replace('www.', '')
        items.append(f'[{host}]({url})')
    return ' '.join(items)


def _fallback_response(payload: dict, fact_check: list[KuybotFactCheckItem] | None = None, search_results: list[dict] | None = None) -> KuybotResponse:
    question = payload.get("question", "")
    news = payload.get("news") or {}
    title = news.get("title") or "la noticia actual"
    summary = news.get("summary") or "Sin resumen disponible."
    claims = news.get("claims") or []
    related = news.get("related_news") or []
    official = _extract_official_sources(payload)
    cited = _unique_urls(
        [item.get("url") for item in related if item.get("url")] +
        [item.url for item in (fact_check or []) if item.url] +
        [item.get("url") for item in (search_results or []) if item.get("url")] +
        [item.get("url") for item in official if item.get("url")]
    )[:10]

    intent = _infer_question_intent(question)

    source_links = _format_source_links(cited)

    if intent == "verification":
        answer = (
            f"🟡 REQUIERE VERIFICACIÓN\n\nLa afirmación sobre \"{title}\" debe evaluarse con contraste entre fuentes y no con una sola referencia. "
            f"El resumen disponible indica que la historia requiere corroboración adicional.\n\n"
            f"Por qué: \n• La noticia presenta afirmaciones relevantes.\n• El análisis previo marca la necesidad de contrastar fuentes.\n• No existe confirmación definitiva a partir de la evidencia disponible.\n\n"
            f"Evidencia: {summary}\n\nFuentes: {source_links}"
        )
    elif intent in {"official_source", "sources"}:
        official_list = ', '.join(item.get('source') or item.get('title') or 'fuente' for item in official[:3]) if official else 'fuentes relacionadas y oficiales'
        answer = (
            f"📚 FUENTES Y CONTEXTO\n\nLa noticia \"{title}\" ya tiene contexto de cobertura y fuentes relacionadas. "
            f"El conjunto más relevante incluye: {official_list}.\n\n"
            f"Esto ayuda a evaluar si la información se sostiene, requiere un matiz o necesita corroboración adicional.\n\nFuentes: {source_links}"
        )
    elif intent == "contrast":
        answer = (
            f"🟠 INFORMACIÓN CONTRADICTORIA\n\nLa investigación requiere comparar la fuente principal con la cobertura relacionada y con fuentes oficiales.\n\n"
            f"La evidencia disponible sugiere que la historia puede tener varias versiones o interpretaciones, por lo que debe revisarse si existen contradicciones antes de asumir una conclusión final.\n\nFuentes: {source_links}"
        )
    else:
        claim_text = claims[0].get("claim") if claims else "la afirmación central"
        answer = (
            f"🧭 CONTEXTO DE INVESTIGACIÓN\n\nEstoy revisando la noticia \"{title}\".\n\n"
            f"La afirmación central a contrastar es: {claim_text}.\n\n"
            f"Resumen del contexto: {summary}\n\n"
            "Lo más útil aquí es separar hechos, interpretaciones y comentarios, luego contrastarlos con fuentes relacionadas y oficiales. El objetivo no es imponer una conclusión, sino mostrar qué está respaldado, qué está cuestionado y qué falta validar.\n\nFuentes: {source_links}"
        )

    return KuybotResponse(
        answer=answer,
        sources=cited,
        fact_check=fact_check or [],
        mode="fallback",
        status="ok",
    )


def _build_source_links(source_items: list[dict] | list[str] | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in source_items or []:
        if isinstance(item, str):
            url = item.strip()
        elif isinstance(item, dict):
            url = (item.get('url') or item.get('link') or '').strip()
        else:
            continue
        if url and url not in seen:
            seen.add(url)
            output.append(url)
    return output
