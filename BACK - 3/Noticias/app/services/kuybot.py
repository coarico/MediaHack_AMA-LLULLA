from __future__ import annotations

import json
import re
from urllib.parse import urlparse
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.news import KuybotFactCheckItem, KuybotResponse
from app.services.research_classifier import get_research_classifier


SYSTEM_PROMPT = """Eres Kuybot, asistente de verificación periodística.

Objetivo:
- Entregar análisis útil para periodistas.
- Diferenciar claramente: confirmado, contradicho, no confirmado y contexto insuficiente.
- Nunca mezclar periodos distintos como contradicción directa.

Formato obligatorio de salida:
1. Resumen
2. Explica cada claim diferente
3. Diferencias clave detectadas
4. Qué falta por confirmar
5. Recomendación periodística inmediata
6. Fuentes consultadas (con URL)

Reglas:
- Escribe en español claro y profesional.
- No inventes datos ni URLs.
- Si no hay evidencia suficiente, dilo explícitamente.
- Priorización de fuentes: oficial > verificación > medios.
"""


def _is_person_profile_question(question: str | None) -> bool:
    q = (question or "").lower()
    person_markers = [
        "quien es", "quién es", "who is", "qué es", "perfil", "biografia", "biografía",
        "trabajo de", "funcion de", "cargo de", "rol de", "es un", "qué hace",
        "qué papel tiene", "quién fue", "quién es el", "quien era"
    ]
    return any(marker in q for marker in person_markers)


def _infer_question_intent(question: str) -> str:
    q = (question or "").lower()

    if _is_person_profile_question(question):
        return "person_profile"

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

    if _is_person_profile_question(question):
        return "level_1"

    if any(term in q for term in ["qué significa", "significado", "define", "explica", "resumen", "contexto", "qué es", "explica el concepto", "resumen del contexto"]):
        return "level_1"

    if any(term in q for term in ["qué dijo el cne", "qué dice el cne", "qué dijo la fiscalía", "qué dijo el ministerio", "fuente oficial", "qué dicen las fuentes oficiales", "dónde aparece", "qué dijo"]):
        return "level_2"

    if any(term in q for term in ["es verdad", "verdad", "falso", "mentira", "confirmado", "desmentido", "verificado", "qué ocurrió realmente", "contradicción", "comparar", "coincide", "diferencia", "evidencia", "qué fuentes respaldan", "qué dicen diferentes medios", "qué pasó realmente"]):
        return "level_3"

    if any(term in q for term in ["fuente", "fuentes", "apoyan", "respaldan", "pruebas", "fact-check", "verificación", "investigación"]):
        return "level_2"

    return "level_1"


def _determine_research_strategy(payload: dict) -> dict:
    """
    Determine the research strategy based on query category and evidence hierarchy.
    
    Returns dict with category, hierarchy_order, and primary_operators.
    """
    classifier = get_research_classifier()
    
    question = payload.get("question") or ""
    news = payload.get("news") or {}
    topic = news.get("title") or ""
    claims = [c.get("claim", "") for c in news.get("verifiable_claims", [])[:3]]
    
    classification = classifier.classify_query(
        query=question,
        topic=topic,
        claims=[{"claim": c} for c in claims]
    )
    
    return {
        "category": classification.get("category", "general"),
        "confidence": classification.get("confidence", 0.5),
        "hierarchy_order": classification.get("hierarchy_order", [6, 3, 7, 5, 4, 8]),
        "primary_operators": classification.get("primary_operators", []),
        "keywords_matched": classification.get("keywords_matched", []),
    }


def _build_search_query(payload: dict) -> str:
    news = payload.get("news") or {}
    question = payload.get("question") or ""
    title = news.get("title") or ""
    claims = " ".join((news.get("main_claims") or [])[:3])
    audit = news.get("audit_summary") or ""
    return " ".join(part for part in [question, title, claims, audit] if part and str(part).strip())


def _build_hierarchical_search_query(payload: dict, max_levels: int = 2) -> list[dict]:
    """
    Build a list of search queries ordered by evidence hierarchy.
    
    Returns list of {"query": str, "level": int, "level_name": str, "primary": bool}
    """
    classifier = get_research_classifier()
    base_query = _build_search_query(payload)
    
    strategy = _determine_research_strategy(payload)
    category = strategy.get("category", "general")
    
    queries = classifier.build_hierarchical_search_query(
        base_query=base_query,
        category=category,
        max_levels=max_levels
    )
    
    # Enrich each query with primary source indicator
    for query in queries:
        query["primary"] = query.get("level", 99) <= 3
    
    return queries


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
    """Estructura claims evaluados sin frases repetidas."""
    claims = payload.get("claim_analysis") or []
    if not claims:
        return "No hay claims."
    lines = []
    status_emoji = {"confirmado": "✓", "contradicho": "✗", "no_confirmado": "?", "contexto_insuficiente": "?"}
    for i, claim in enumerate(claims[:5], 1):
        claim_text = claim.get("claim", "N/A")
        status_dict = claim.get("status", {})
        status_val = status_dict.get("status", "no_confirmado") if isinstance(status_dict, dict) else "no_confirmado"
        reasoning = status_dict.get("reasoning", "") if isinstance(status_dict, dict) else ""
        emoji = status_emoji.get(status_val, "?")
        lines.append(f"{emoji} [{status_val.upper()}] {claim_text}")
        if reasoning and reasoning.strip():
            lines.append(f"   {reasoning[:150]}")
    return "\n".join(lines)


def _format_short_url(url: str | None) -> str:
    """Convierte URL en formato [Leer mas](url)."""
    if not url:
        return ""
    return f"[Leer mas]({url})"


async def ask_kuybot(question: str, news: dict | None, history: list[dict] | None = None) -> KuybotResponse:
    payload = _build_context(news, question, history or [])
    intent = _infer_question_intent(question)
    research_level = _classify_research_level(question)
    research_strategy = _determine_research_strategy(payload)
    
    payload["intent"] = intent
    payload["research_level"] = research_level
    payload["research_strategy"] = research_strategy
    payload["search_query"] = _build_search_query(payload)

    fact_check: list[KuybotFactCheckItem] = []
    search_results: list[dict] = []
    structured_claims = _extract_claims_from_news(payload)

    if intent == "person_profile":
        return _build_person_profile_response(payload, fact_check, search_results)

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
    
    question = payload.get("question", "")
    news_title = payload.get("news", {}).get("title", "")
    claims_summary = _build_claim_summary(payload)
    
    # Gemini redacta un resumen técnico breve; la estructura final se arma localmente.
    simple_prompt = f"""Pregunta del periodista: {question}
Noticia: {news_title}

Claims evaluados:
{claims_summary}

Instrucción:
Redacta SOLO un resumen técnico breve (2 a 4 líneas) para alimentar una respuesta estructurada.
No incluyas encabezados, ni bibliografía, ni listas largas."""
    
    full_prompt = SYSTEM_PROMPT + "\n\n" + simple_prompt

    response = client.models.generate_content(model=model_name, contents=full_prompt)
    model_summary = getattr(response, "text", None) or (
        response.candidates[0].content.parts[0].text if getattr(response, "candidates", None) else "No se pudo obtener respuesta del modelo."
    )

    answer, sources = _compose_structured_answer(payload, fact_check, search_results, model_summary)

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

    base_query = _build_search_query(payload)
    if not base_query:
        return []

    # Build hierarchical search queries
    hierarchical_queries = _build_hierarchical_search_query(payload, max_levels=2)
    
    all_results = []
    seen_urls = set()
    
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            # Try primary sources first, then secondary
            for query_item in hierarchical_queries:
                search_query = query_item.get("query", "")
                level = query_item.get("level", 99)
                level_name = query_item.get("level_name", "")
                
                if not search_query:
                    continue
                
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": settings.google_search_api_key,
                        "cx": settings.google_search_cx,
                        "q": search_query,
                        "num": 4,
                    },
                    timeout=10,
                )
                
                if response.status_code != 200:
                    continue
                
                items = response.json().get("items") or []
                
                for item in items[:4]:
                    url = item.get("link")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        result = {
                            "title": item.get("title"),
                            "url": url,
                            "snippet": item.get("snippet"),
                            "source": item.get("displayLink"),
                            "evidence_level": level,
                            "evidence_level_name": level_name,
                        }
                        all_results.append(result)
                
                # If we found results at this level, we can stop searching lower levels
                if all_results and level <= 3:
                    break
        
        return all_results[:8]  # Return top 8 results from all levels
        
    except Exception:
        return []


def _extract_official_sources(payload: dict) -> list[dict]:
    """
    Extract and prioritize official sources using evidence hierarchy.
    
    Sources are ranked by evidence level (0-8), with lower numbers being more authoritative.
    """
    classifier = get_research_classifier()
    related = payload.get("news", {}).get("related_news") or []
    
    # Legacy priority mapping (fallback for unclassified sources)
    legacy_priorities = {
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
        source_name = item.get("source") or item.get("source_name") or "Fuente relacionada"
        url = item.get("url") or ""
        
        # Try to get evidence level from hierarchy
        if url:
            domain = url.split("://")[-1].split("/")[0]
            evidence_level = classifier.get_evidence_level(domain)
            if evidence_level is not None:
                priority = evidence_level
            else:
                priority = legacy_priorities.get(source_type, 99)
        else:
            priority = legacy_priorities.get(source_type, 99) if source_type else 99
        
        ranked.append((priority, {
            "title": item.get("title"),
            "url": url,
            "source": source_name,
            "source_type": item.get("source_type"),
            "evidence_level": priority if isinstance(priority, int) and priority <= 8 else None,
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
        return ''
    items: list[str] = []
    for url in urls[:3]:
        items.append(_format_short_url(url))
    return ' '.join(items)


def _status_label(value: str) -> str:
    mapping = {
        "confirmado": "Confirmado",
        "contradicho": "Contradicho",
        "no_confirmado": "No confirmado",
        "contexto_insuficiente": "Contexto insuficiente",
    }
    return mapping.get(value, value.replace("_", " ").title())


def _build_claim_lines(payload: dict) -> list[str]:
    claims = payload.get("claim_analysis") or []
    if not claims:
        return ["- No se detectaron claims verificables en este contexto."]

    lines: list[str] = []
    for claim in claims[:6]:
        status = claim.get("status") if isinstance(claim.get("status"), dict) else {}
        status_value = status.get("status", "no_confirmado")
        reasoning = status.get("reasoning", "Sin detalle de verificación.")
        lines.append(f"- [{_status_label(status_value)}] {claim.get('claim', 'Claim sin texto')}")
        lines.append(f"  Evidencia: {reasoning}")
    return lines


def _build_journalist_insights(payload: dict) -> list[str]:
    claims = payload.get("claim_analysis") or []
    if not claims:
        return [
            "- No hay claims suficientes; primero necesitas más texto verificable de la noticia.",
            "- Prioriza recopilar comunicado oficial y registro documental del hecho.",
        ]

    contradicted = sum(1 for c in claims if isinstance(c.get("status"), dict) and c["status"].get("status") == "contradicho")
    no_confirmed = sum(1 for c in claims if isinstance(c.get("status"), dict) and c["status"].get("status") == "no_confirmado")
    temporal_issues = sum(1 for c in claims if isinstance(c.get("status"), dict) and c["status"].get("status") == "contexto_insuficiente")

    notes = [
        f"- Claims con contradicción directa: {contradicted}.",
        f"- Claims sin evidencia oficial suficiente: {no_confirmed}.",
        f"- Claims con posible desfase temporal/contextual: {temporal_issues}.",
        "- Siguiente paso recomendado: pedir documento, resolución o acta oficial para los claims no confirmados.",
    ]
    return notes


def _build_sources_section(payload: dict, fact_check: list[KuybotFactCheckItem], search_results: list[dict]) -> tuple[list[str], list[str]]:
    official = _extract_official_sources(payload)
    related = payload.get("news", {}).get("related_news") or []

    official_urls = [item.get("url") for item in official if item.get("url")]
    fact_urls = [item.url for item in fact_check if item.url]
    search_urls = [item.get("url") for item in search_results if item.get("url")]
    related_urls = [item.get("url") for item in related if item.get("url")]

    all_urls = _unique_urls(official_urls + fact_urls + search_urls + related_urls)

    lines: list[str] = []
    if official_urls:
        for url in _unique_urls(official_urls)[:4]:
            lines.append(f"- Oficial: {url}")
    if fact_urls:
        for url in _unique_urls(fact_urls)[:3]:
            lines.append(f"- Fact-check: {url}")
    if search_urls:
        for url in _unique_urls(search_urls)[:3]:
            lines.append(f"- Cobertura relacionada: {url}")
    if not lines:
        lines.append("- No se encontraron URLs verificables en esta consulta.")

    return all_urls[:10], lines


def _compose_structured_answer(payload: dict, fact_check: list[KuybotFactCheckItem], search_results: list[dict], summary_text: str) -> tuple[str, list[str]]:
    claim_lines = _build_claim_lines(payload)
    insight_lines = _build_journalist_insights(payload)
    source_urls, source_lines = _build_sources_section(payload, fact_check, search_results)

    claims = payload.get("claim_analysis") or []
    contradicted = sum(1 for c in claims if isinstance(c.get("status"), dict) and c["status"].get("status") == "contradicho")
    confirmed = sum(1 for c in claims if isinstance(c.get("status"), dict) and c["status"].get("status") == "confirmado")

    differences_line = (
        f"Se detectaron {contradicted} claim(s) contradicho(s) y {confirmed} claim(s) confirmado(s) en el mismo contexto temporal."
        if claims else
        "No hay suficientes claims evaluados para medir diferencias con precisión."
    )

    answer = (
        "1. Resumen\n"
        f"{summary_text.strip() if summary_text and summary_text.strip() else 'Se contrastó la noticia por claims y por temporalidad para evitar contradicciones falsas.'}\n\n"
        "2. Explica cada claim diferente\n"
        f"{'\n'.join(claim_lines)}\n\n"
        "3. Diferencias clave detectadas\n"
        f"- {differences_line}\n\n"
        "4. Qué falta por confirmar\n"
        f"- {next((line for line in insight_lines if 'sin evidencia oficial' in line.lower()), 'No hay registro oficial suficiente para algunos claims.').lstrip('- ').strip()}\n"
        "- Para cerrar verificación, cruza cada cifra con boletín o acta oficial.\n\n"
        "5. Recomendación periodística inmediata\n"
        f"{'\n'.join(insight_lines)}\n\n"
        "6. Fuentes consultadas (con URL)\n"
        f"{'\n'.join(source_lines)}"
    )

    return answer, source_urls


def _build_person_profile_response(payload: dict, fact_check: list[KuybotFactCheckItem] | None = None, search_results: list[dict] | None = None) -> KuybotResponse:
    news = payload.get("news") or {}
    title = news.get("title") or "La noticia analizada"
    summary = news.get("summary") or "Sin resumen disponible."
    question = payload.get("question") or ""
    related = news.get("related_news") or []
    official = _extract_official_sources(payload)
    cited = _unique_urls(
        [item.get("url") for item in related if item.get("url")] +
        [item.url for item in (fact_check or []) if item.url] +
        [item.get("url") for item in (search_results or []) if item.get("url")] +
        [item.get("url") for item in official if item.get("url")]
    )[:10]

    person_name = re.search(r"(?:quien es|quién es|who is)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+)*)", question or "")
    subject = person_name.group(1).strip() if person_name else "la persona mencionada"

    answer = (
        f"Perfil público\n"
        f"{subject} aparece en esta noticia en relación con la administración pública y el contexto político del caso.\n\n"
        f"Qué dice la noticia\n"
        f"{title}\n\n"
        f"Resumen\n"
        f"{summary}\n\n"
        f"Qué falta verificar\n"
        "Para confirmar su perfil completo, su cargo exacto o su trayectoria institucional, es necesario contrastar la información con fuentes oficiales, como comunicados del Gobierno, la Cancillería o documentos institucionales.\n\n"
        f"Fuentes relevantes\n{_format_source_links(cited)}"
    )

    return KuybotResponse(
        answer=answer,
        sources=cited,
        fact_check=fact_check or [],
        mode="fallback",
        status="ok",
    )


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

    if intent == "person_profile":
        return _build_person_profile_response(payload, fact_check, search_results)

    summary_hint = summary if summary else f"Se revisó la noticia '{title}' para responder: {question}"
    answer, composed_sources = _compose_structured_answer(payload, fact_check or [], search_results or [], summary_hint)
    if composed_sources:
        cited = _unique_urls(composed_sources + cited)[:10]

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
