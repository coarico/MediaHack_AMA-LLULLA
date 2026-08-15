from __future__ import annotations

import json
import re
from urllib.parse import urlparse
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.news import KuybotFactCheckItem, KuybotResponse


SYSTEM_PROMPT = """Eres Kuybot, asistente de investigación y verificación periodística de AMA LLU IA.

Flujo operativo obligatorio:
1) Lee la noticia auditada y la pregunta del usuario.
2) Extrae los claims verificables de la noticia, uno por uno.
3) Para cada claim identifica: entidades, evento, contexto temporal y tipo.
4) Investiga cada claim de manera independiente con evidencia de:
   - Google Custom Search (Google Search Engine)
   - Fact Check Tools API
   - Fuentes oficiales institucionales
   - Fuentes relacionadas de la noticia
5) Antes de declarar contradicción, verifica:
   - mismo evento
   - mismo periodo temporal
   - misma entidad
   - mismo contexto institucional
6) Si una fuente pertenece a un evento anterior o distinto, solo úsala como contexto histórico, no como contradicción directa.
7) Clasifica cada claim como: confirmado, contradicho, no confirmado o contexto insuficiente.
8) No conviertas la noticia en un único bloque. Debes contrastar cada afirmación por separado.
9) Produces la respuesta final con esta estructura exacta:
   - Conclusión
   - ¿Por qué se concluye así?
   - Evidencia
   - Fuentes

Reglas:
- No inventes fuentes, URLs, citas, fechas ni instituciones.
- Si no hay evidencia suficiente, dilo claramente.
- No digas que algo es falso solo porque no aparece una cifra o fecha concreta; di que no hubo evidencia suficiente para confirmarlo.
- No generalices un error de un claim para declarar toda la noticia falsa.
- Prioriza fuentes oficiales y verificadas sobre rumores o análisis no contrastados.
- Usa una redacción breve, clara y útil para reportaje periodístico.
- No muestres texto fijo, plantillas vacías ni mensajes predeterminados del sistema.
- La respuesta final debe estar escrita como un análisis real del contexto, no como un chatbot genérico.
"""


def _infer_question_intent(question: str) -> str:
    q = (question or "").lower()

    if any(term in q for term in ["es verdad", "verdad", "falso", "mentira", "confirmado", "desmentido", "verificado", "qué pasó", "qué ocurrió", "qué sucedió", "contrad", "compare", "diferencia", "evidencia", "respaldan", "apoyan", "coincide"]):
        return "verification"
    if any(term in q for term in ["fuente oficial", "qué dijo", "dice el cne", "dice la fiscalía", "fuentes oficiales", "institución", "ministerio", "qué dicen", "documento oficial"]):
        return "official_source"
    if any(term in q for term in ["contrario", "opuesto", "coincide", "compare", "compar", "diferencia", "contradic"]):
        return "contrast"
    if any(term in q for term in ["fuente", "respald", "apoyan", "qué fuentes", "documentan", "evidencia", "pruebas", "verificación"]):
        return "sources"
    if any(term in q for term in ["antecedente", "historia", "pasado", "anteriormente", "relacionado", "noticias relacionadas"]):
        return "background"
    if any(term in q for term in ["contexto", "significado", "qué significa", "explica", "resumen", "define"]):
        return "context"
    return "general"


def _classify_research_level(question: str | None) -> str:
    q = (question or "").lower()

    if any(term in q for term in ["qué significa", "significado", "define", "explica", "resumen", "contexto", "qué es", "explica el concepto", "resumen del contexto"]):
        return "level_1"

    if any(term in q for term in ["qué dijo el cne", "qué dice el cne", "qué dijo la fiscalía", "qué dijo el ministerio", "fuente oficial", "qué dicen las fuentes oficiales", "dónde aparece", "qué dijo"]):
        return "level_2"

    if any(term in q for term in ["es verdad", "verdad", "falso", "mentira", "confirmado", "desmentido", "verificado", "qué ocurrió realmente", "contradicción", "comparar", "coincide", "diferencia", "evidencia", "qué fuentes respaldan", "qué dicen diferentes medios", "qué pasó realmente"]):
        return "level_3"

    if any(term in q for term in ["fuente", "fuentes", "apoyan", "respaldan", "pruebas", "fact-check", "verificación", "investigación"]):
        return "level_2"

    return "level_1"


def _build_search_query(payload: dict) -> str:
    news = payload.get("news") or {}
    question = payload.get("question") or ""
    title = news.get("title") or ""
    claims = " ".join((news.get("main_claims") or [])[:3])
    audit = news.get("audit_summary") or ""
    return " ".join(part for part in [question, title, claims, audit] if part and str(part).strip())


def _extract_years(text: str | None) -> list[str]:
    if not text:
        return []
    return re.findall(r"\b(?:19|20)\d{2}\b", text)


def _normalise_claim_types(claim: str) -> str:
    value = (claim or "").lower()
    if re.search(r"\b\d+(?:[.,]\d+)?\s*%\b|\b\d+\s+de\s+\d+\b|\b\d+\s+solicitudes\b|\b\d+\s+alianzas\b", value):
        return "numeric"
    if re.search(r"\b(?:29\s+de\s+noviembre|noviembre\s+de\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\b", value):
        return "date"
    if any(term in value for term in ["aprob", "rechaz", "suspend", "inscrib", "anunci", "elect", "candid", "alianz", "fecha"]):
        return "event"
    if any(term in value for term in ["ley", "resolucion", "resolución", "decreto", "declar", "mandato", "sancion", "disposicion"]):
        return "legal_status"
    if any(term in value for term in ["dice", "dijo", "según", "afirma", "manifest", "declar"]):
        return "statement"
    return "statement"


def _extract_entities(text: str | None) -> list[str]:
    if not text:
        return []
    entities = re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){0,2}\b", text)
    return [entity.strip() for entity in entities if entity.strip()][:8]


def _extract_claims_from_news(payload: dict) -> list[dict]:
    news = payload.get("news") or {}
    raw_claims: list[str] = []

    for item in news.get("claims") or []:
        if isinstance(item, dict):
            claim_text = item.get("claim") or item.get("text") or ""
            if claim_text:
                raw_claims.append(str(claim_text))
        elif item:
            raw_claims.append(str(item))

    for item in news.get("main_claims") or []:
        raw_claims.append(str(item))

    title = news.get("title") or ""
    summary = news.get("summary") or ""
    if title and title not in raw_claims:
        raw_claims.append(title)
    if summary and summary not in raw_claims:
        raw_claims.append(summary)

    structured: list[dict] = []
    seen: set[str] = set()
    for index, claim in enumerate(raw_claims[:8], start=1):
        clean = re.sub(r"\s+", " ", str(claim)).strip()
        if not clean or clean.lower() in seen:
            continue
        seen.add(clean.lower())
        event = "" if not clean else clean[:120]
        date_context = " ".join(_extract_years(clean)[:3])
        structured.append({
            "claimId": f"claim-{index}",
            "claim": clean,
            "entities": _extract_entities(clean),
            "event": event,
            "dateContext": date_context or "contexto_general",
            "type": _normalise_claim_types(clean),
        })
    return structured


def _normalise_evidence_item(item: Any) -> dict:
    if isinstance(item, dict):
        return {
            "title": item.get("title") or item.get("source") or item.get("publisher") or "",
            "snippet": item.get("snippet") or item.get("text") or item.get("summary") or "",
            "url": item.get("url") or "",
            "source": item.get("source") or item.get("publisher") or "",
        }
    if hasattr(item, "url"):
        return {
            "title": getattr(item, "publisher", None) or getattr(item, "claimant", None) or "",
            "snippet": getattr(item, "text", None) or "",
            "url": getattr(item, "url", None) or "",
            "source": getattr(item, "publisher", None) or getattr(item, "claimant", None) or "",
        }
    return {"title": "", "snippet": "", "url": "", "source": ""}


def _claim_matches_period(claim: dict, evidence: dict) -> bool:
    claim_years = _extract_years(claim.get("dateContext") or claim.get("claim") or "")
    evidence_text = f"{evidence.get('title') or ''} {evidence.get('snippet') or ''} {evidence.get('source') or ''}"
    evidence_years = _extract_years(evidence_text)
    if not claim_years:
        return True
    if not evidence_years:
        return True
    return any(year in claim_years for year in evidence_years) or any(int(year) in range(int(claim_years[0]) - 1, int(claim_years[0]) + 2) for year in evidence_years)


def _evaluate_claim_status(claim: dict, evidence: list[Any], official_sources: list[dict] | None = None) -> dict:
    claim_event = (claim.get("event") or "").lower()
    claim_years = _extract_years(claim.get("dateContext") or claim.get("claim") or "")
    official_sources = official_sources or []
    evidence_items = [_normalise_evidence_item(item) for item in evidence]

    if not evidence_items:
        return {
            "status": "no_confirmado",
            "reasoning": "No se encontró evidencia suficiente para verificar este claim con fuentes actuales.",
        }

    same_period: list[dict] = []
    different_period_context: list[dict] = []
    direct_contradictions: list[dict] = []
    for item in evidence_items:
        text = f"{item.get('title') or ''} {item.get('snippet') or ''} {item.get('source') or ''}".lower()
        relevant_terms = ["alianz", "eleccion", "candid", "fecha", "inscrip", "suspend", "pedido"]
        claim_tokens = [token for token in relevant_terms if token in claim_event]
        same_event = bool(
            (claim_event and (claim_event in text or bool(claim_tokens and any(token in text for token in claim_tokens))))
            or (not claim_event and any(token in text for token in relevant_terms))
        )
        year_match = _claim_matches_period(claim, item)
        evidence_years = _extract_years(f"{item.get('title') or ''} {item.get('snippet') or ''}")

        if same_event and year_match:
            same_period.append(item)
            if any(word in text for word in ["rechaz", "no", "inexist", "contrad", "difer", "no coincide", "falso"]):
                direct_contradictions.append(item)
        elif same_event and claim_years and evidence_years and any(str(year) in evidence_years for year in claim_years) is False:
            different_period_context.append(item)

    if claim_years and same_period:
        official_match = any((src.get("source") or "").lower() in {"cne", "gobierno", "institucion"} for src in official_sources)
        if direct_contradictions:
            return {
                "status": "contradicho",
                "reasoning": f"Se encontró evidencia que contradice la afirmación para el mismo evento y periodo temporal. El contexto de {claim_years[0]} no coincide con fuentes que apuntan a un escenario distinto.",
                "official_match": official_match,
            }
        return {
            "status": "confirmado",
            "reasoning": f"La evidencia disponible coincide con el mismo evento y periodo temporal para {claim_years[0]}.",
            "official_match": official_match,
        }

    if claim_years and different_period_context:
        context_years = sorted({year for item in different_period_context for year in _extract_years(f"{item.get('title') or ''} {item.get('snippet') or ''}")})
        context_text = ", ".join(context_years) if context_years else "un periodo anterior o distinto"
        return {
            "status": "contexto_insuficiente",
            "reasoning": f"La evidencia disponible refiere al mismo tipo de evento, pero a un periodo temporal distinto del de {claim_years[0]} (contexto observado: {context_text}). No puede utilizarse como contradicción directa.",
        }

    return {
        "status": "no_confirmado",
        "reasoning": f"No encontramos evidencia oficial suficiente para confirmar o rechazar este claim del mismo contexto temporal y institucional.",
    }


def _build_claim_summary(payload: dict) -> str:
    claims = payload.get("claim_analysis") or []
    if not claims:
        return "No se generó un resumen por claim para esta verificación."

    lines = []
    for claim in claims:
        status = claim.get("status", {})
        label = status.get("status", "no_confirmado") if isinstance(status, dict) else "no_confirmado"
        reasoning = status.get("reasoning", "Sin justificación detallada.") if isinstance(status, dict) else "Sin justificación detallada."
        lines.append(f"- {claim.get('claim') or 'Claim no identificado'} → {label}. {reasoning}")
    return "\n".join(lines)


async def ask_kuybot(question: str, news: dict | None, history: list[dict] | None = None) -> KuybotResponse:
    payload = _build_context(news, question, history or [])
    intent = _infer_question_intent(question)
    research_level = _classify_research_level(question)
    payload["intent"] = intent
    payload["research_level"] = research_level
    payload["search_query"] = _build_search_query(payload)

    fact_check: list[KuybotFactCheckItem] = []
    search_results: list[dict] = []
    structured_claims = _extract_claims_from_news(payload)

    if research_level in {"level_2", "level_3"}:
        fact_check = await _search_fact_checks(payload)

    if research_level == "level_3":
        search_results = await _search_web_results(payload)

    if research_level == "level_2":
        official_candidates = _extract_official_sources(payload)
        if official_candidates:
            payload["preferred_official_source"] = official_candidates[0]

    official_sources = _extract_official_sources(payload)
    evidence_pack = [
        _normalise_evidence_item(item)
        for item in [
            *search_results,
            *[item.model_dump(exclude_none=True) for item in fact_check],
            *official_sources,
        ]
    ]
    payload["claim_analysis"] = [
        {
            **claim,
            "status": _evaluate_claim_status(claim, evidence_pack, official_sources),
        }
        for claim in structured_claims[:5]
    ]

    payload["evidence"] = {
        "fact_checks": [item.model_dump(exclude_none=True) for item in fact_check],
        "search_results": search_results,
        "official_sources": official_sources,
        "intent": intent,
        "research_level": research_level,
        "claims": payload["claim_analysis"],
    }

    if research_level == "level_3" and payload.get("claim_analysis"):
        claim_summary = _build_claim_summary(payload)
        answer = (
            "Conclusión\n"
            "La verificación debe hacerse por claims, no por una sola conclusión global. El contraste entre fuentes debe respetar entidad, evento y temporalidad.\n\n"
            "¿Por qué se concluye así?\n"
            "- Los datos de 2023 o de otros periodos solo pueden usarse como contexto histórico, no como contradicción directa de un evento programado para 2026.\n"
            "- Cuando la evidencia oficial o institucional refiere al mismo tipo de evento, pero en un periodo distinto, la respuesta correcta es 'contexto insuficiente' o 'no confirmado', no 'falso' ni 'inexistente'.\n\n"
            "Evidencia\n"
            f"{claim_summary}\n\n"
            "Fuentes\n"
            f"{_format_source_links(_unique_urls([item.get('url') for item in search_results if item.get('url')] + [item.url for item in fact_check if item.url] + [item.get('url') for item in official_sources if item.get('url')]))}"
        )
        return KuybotResponse(
            answer=answer,
            sources=_unique_urls([item.get('url') for item in search_results if item.get('url')] + [item.url for item in fact_check if item.url] + [item.get('url') for item in official_sources if item.get('url')])[:10],
            fact_check=fact_check,
            mode="fallback",
            status="ok",
        )

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

    structured_claims = _extract_claims_from_news({
        "news": {
            "title": article.get("title"),
            "summary": analysis.get("summary"),
            "main_claims": analysis.get("main_claims", []),
            "related_news": related_news,
            "claims": [{"claim": item.get("claim"), "type": item.get("type")} for item in verifiable_claims[:5]],
        }
    })

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
            "structured_claims": structured_claims,
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


async def _search_fact_checks(payload: dict) -> list[KuybotFactCheckItem]:
    if not settings.fact_check_api_key:
        return []

    query = _build_search_query(payload)
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

    query = _build_search_query(payload)
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
