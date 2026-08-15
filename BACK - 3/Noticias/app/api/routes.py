from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.core.security import UnsafeUrlError, validate_public_http_url
from app.schemas.news import AnalysisListItem, AnalyzeRequest, AnalyzeResponse, KuybotRequest, KuybotResponse, SourceInput
from app.services.ai_analyzer import analyze_article_with_metadata
from app.services.article_extractor import ExtractionError, extract_article
from app.services.article_fetcher import FetchError, fetch_html
from app.services.claims_extractor import extract_verifiable_claims
from app.services.claim_contrast import build_claim_contrasts
from app.services.content_quality import evaluate_content_quality
from app.services.content_attribution import build_content_attribution
from app.services.cross_source import build_cross_source_check
from app.services.editorial_metadata import build_editorial_metadata
from app.services.firestore_store import new_analysis_id, now_utc, store
from app.services.gender_impact import assess_gender_impact
from app.services.information_relevance import classify_information_relevance
from app.services.kuybot import ask_kuybot
from app.services.llm_context import build_llm_compact_context
from app.services.news_reliability import build_news_reliability_assessment
from app.services.related_search import iter_related_news_batches, search_related_news
from app.services.source_classifier import classify_source
from app.services.source_verification import build_source_verification
from app.services.url_content_classifier import classify_url_content
from app.services.url_risk import evaluate_url_risk
from app.services.url_technical_report import build_url_technical_report
from app.services.url_trust import build_url_trust_assessment


router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_news(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    try:
        safe_url = validate_public_http_url(str(request.url))
        fetched = await fetch_html(safe_url)
        article = extract_article(fetched.final_url, fetched.html)
        source_classification = classify_source(safe_url, article.source_domain)
        content_attribution = build_content_attribution(safe_url, article, source_classification)
        content_quality = evaluate_content_quality(article)
        verifiable_claims = extract_verifiable_claims(article)
        llm_compact_context = build_llm_compact_context(article, verifiable_claims)
        analysis, llm_execution = await analyze_article_with_metadata(article, llm_compact_context)
        editorial_metadata = build_editorial_metadata(request, article, source_classification, analysis, content_attribution)
        information_relevance = classify_information_relevance(article, analysis)
        related_news = []
        url_risk_signals = evaluate_url_risk(safe_url, fetched.final_url, fetched.url_health)
        url_trust_assessment = build_url_trust_assessment(fetched.url_health, url_risk_signals)
        url_content_classification = classify_url_content(
            fetched.final_url,
            article,
            source_classification,
            content_attribution,
            content_quality,
        )
        claim_contrasts = []
        gender_impact_assessment = assess_gender_impact(article, analysis)
        cross_source_check = build_cross_source_check(related_news)
        source_verification = build_source_verification(source_classification, content_attribution, cross_source_check)
        url_technical_report = build_url_technical_report(
            safe_url,
            fetched.final_url,
            fetched.url_health,
            url_trust_assessment,
            url_content_classification,
            source_verification,
            url_risk_signals,
        )
        news_reliability_assessment = build_news_reliability_assessment(
            source_classification,
            source_verification,
            url_trust_assessment,
            url_content_classification,
            content_quality,
            cross_source_check,
            analysis,
        )
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FetchError, ExtractionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error analizando noticia: {exc}") from exc

    response = AnalyzeResponse(
        id=new_analysis_id(),
        status="processing",
        created_at=now_utc(),
        updated_at=now_utc(),
        source_input=SourceInput(original_url=safe_url, final_url=fetched.final_url),
        editorial_metadata=editorial_metadata,
        content_attribution=content_attribution,
        source_verification=source_verification,
        information_relevance=information_relevance,
        url_health=fetched.url_health,
        url_trust_assessment=url_trust_assessment,
        url_content_classification=url_content_classification,
        news_reliability_assessment=news_reliability_assessment,
        url_technical_report=url_technical_report,
        url_risk_signals=url_risk_signals,
        article=article,
        content_quality=content_quality,
        source_classification=source_classification,
        analysis=analysis,
        llm_compact_context=llm_compact_context,
        llm_execution=llm_execution,
        verifiable_claims=verifiable_claims,
        claim_contrasts=claim_contrasts,
        gender_impact_assessment=gender_impact_assessment,
        cross_source_check=cross_source_check,
        risk_assessment=_build_risk_assessment(
            analysis,
            fetched.url_health,
            len(related_news),
            url_risk_signals,
            content_quality,
            cross_source_check,
        ),
        audit=_build_audit_metadata(
            analysis,
            editorial_metadata,
            information_relevance,
            source_classification,
            fetched.url_health,
            len(related_news),
            url_risk_signals,
            content_quality,
            verifiable_claims,
            llm_compact_context,
            llm_execution,
            cross_source_check,
            url_content_classification,
            url_technical_report,
            gender_impact_assessment,
            news_reliability_assessment,
        ),
        related_news=related_news,
    )
    saved = await store.save_analysis(response)
    background_tasks.add_task(_complete_related_analysis, saved)
    return saved


async def _complete_related_analysis(response: AnalyzeResponse) -> None:
    try:
        related_news = []
        async for batch in iter_related_news_batches(
            response.analysis,
            response.source_input.final_url or response.source_input.original_url,
            min_batch_size=2,
        ):
            related_news.extend(batch)
            _refresh_related_sections(response, related_news, final_status="processing")
            await store.update_analysis(response)

        _refresh_related_sections(response, related_news, final_status="completed")
        await store.update_analysis(response)
    except Exception:
        response.status = "failed"
        response.updated_at = now_utc()
        await store.update_analysis(response)


def _refresh_related_sections(response: AnalyzeResponse, related_news, final_status: str) -> None:
    claim_contrasts = build_claim_contrasts(response.verifiable_claims, related_news)
    cross_source_check = build_cross_source_check(related_news)
    source_verification = build_source_verification(
        response.source_classification,
        response.content_attribution,
        cross_source_check,
    )
    url_technical_report = build_url_technical_report(
        response.source_input.original_url,
        response.source_input.final_url or response.source_input.original_url,
        response.url_health,
        response.url_trust_assessment,
        response.url_content_classification,
        source_verification,
        response.url_risk_signals,
    )
    news_reliability_assessment = build_news_reliability_assessment(
        response.source_classification,
        source_verification,
        response.url_trust_assessment,
        response.url_content_classification,
        response.content_quality,
        cross_source_check,
        response.analysis,
    )
    response.source_verification = source_verification
    response.cross_source_check = cross_source_check
    response.claim_contrasts = claim_contrasts
    response.url_technical_report = url_technical_report
    response.news_reliability_assessment = news_reliability_assessment
    response.risk_assessment = _build_risk_assessment(
        response.analysis,
        response.url_health,
        len(related_news),
        response.url_risk_signals,
        response.content_quality,
        cross_source_check,
    )
    response.audit = _build_audit_metadata(
        response.analysis,
        response.editorial_metadata,
        response.information_relevance,
        response.source_classification,
        response.url_health,
        len(related_news),
        response.url_risk_signals,
        response.content_quality,
        response.verifiable_claims,
        response.llm_compact_context,
        response.llm_execution,
        cross_source_check,
        response.url_content_classification,
        url_technical_report,
        response.gender_impact_assessment,
        news_reliability_assessment,
    )
    response.related_news = related_news
    response.status = final_status
    response.updated_at = now_utc()


@router.post("/kuybot", response_model=KuybotResponse)
async def ask_news_kuybot(request: KuybotRequest) -> KuybotResponse:
    try:
        return await ask_kuybot(
            request.question,
            request.news,
            [message.model_dump(mode="json") for message in request.history],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generando respuesta de Kuybot: {exc}") from exc


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str) -> dict:
    result = await store.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analisis no encontrado.")
    return result


@router.get("/analysis", response_model=list[AnalysisListItem])
async def list_analyses(limit: int = Query(default=20, ge=1, le=100)) -> list[AnalysisListItem]:
    return await store.list_analyses(limit=limit)


@router.get("/keywords", response_model=list[str])
async def list_keywords(limit: int = Query(default=30, ge=1, le=100)) -> list[str]:
    analyses = await store.list_analyses(limit=100)
    counts: dict[str, int] = {}
    for item in analyses:
        for keyword in item.keywords:
            counts[keyword] = counts.get(keyword, 0) + 1
    return [keyword for keyword, _ in sorted(counts.items(), key=lambda row: row[1], reverse=True)[:limit]]


def _build_risk_assessment(
    analysis,
    url_health,
    related_count: int,
    url_risk_signals,
    content_quality,
    cross_source_check,
):
    from app.schemas.news import RiskAssessment

    score = max(0, min(100, 100 - analysis.credibility.score))
    reasons = []
    if url_health.is_disconnected:
        score = max(score, 85)
        reasons.append("El link esta desconectado o no es alcanzable.")
    if related_count == 0:
        score = max(score, 55)
        reasons.append("No se encontraron noticias relacionadas con la configuracion actual.")
    if analysis.clickbait.score >= 60:
        reasons.append("El contenido tiene senales altas de clickbait.")
    if analysis.information_gaps:
        reasons.append("La noticia tiene informacion faltante relevante para verificar.")
    if content_quality.quality_score < 50:
        score = max(score, 60)
        reasons.append("La calidad estructural del articulo es baja.")
    if cross_source_check.coverage_status == "no_related_coverage":
        score = max(score, 60)
        reasons.append("No se detecto cobertura relacionada para contrastar el contenido.")
    for signal in url_risk_signals:
        if signal.severity == "alta":
            score = max(score, 75)
        elif signal.severity == "media":
            score = max(score, 55)
        reasons.append(signal.explanation)
    reasons.extend(analysis.manipulation_signals[:3])

    has_high_url_risk = any(signal.severity == "alta" for signal in url_risk_signals)
    has_related_coverage = related_count > 0 or cross_source_check.coverage_status in {"multiple_sources", "single_source"}
    if (
        not url_health.is_disconnected
        and not has_high_url_risk
        and has_related_coverage
        and content_quality.quality_score >= 70
        and analysis.clickbait.score < 60
    ):
        score = min(score, 55)

    if score >= 85:
        level = "critico"
    elif score >= 65:
        level = "alto"
    elif score >= 35:
        level = "medio"
    else:
        level = "bajo"

    return RiskAssessment(
        score=score,
        level=level,
        fraud_or_disinformation_risk=level,
        reasons=reasons[:8],
        cannot_conclude_fraud=True,
    )


def _build_audit_metadata(
    analysis,
    editorial_metadata,
    information_relevance,
    source_classification,
    url_health,
    related_count: int,
    url_risk_signals,
    content_quality,
    verifiable_claims,
    llm_compact_context,
    llm_execution,
    cross_source_check,
    url_content_classification,
    url_technical_report,
    gender_impact_assessment,
    news_reliability_assessment,
):
    from app.schemas.news import AuditEvidenceItem, AuditMetadata

    evidence_items = [
        AuditEvidenceItem(
            type="source",
            label="Tipo de fuente",
            value=source_classification.communication_type,
            severity="media",
        ),
        AuditEvidenceItem(
            type="source",
            label="Plataforma",
            value=editorial_metadata.platform,
            severity="media",
        ),
        AuditEvidenceItem(
            type="source",
            label="Quien publica",
            value=editorial_metadata.publisher_type,
            severity="media",
        ),
        AuditEvidenceItem(
            type="source",
            label="Eje tematico",
            value=editorial_metadata.thematic_axis or "Sin clasificar",
            severity="media",
        ),
        AuditEvidenceItem(
            type="risk",
            label="Relevancia electoral",
            value=f"{information_relevance.domain} / {information_relevance.relation_type} / {information_relevance.relevance_score}",
            severity="alta" if information_relevance.is_relevant else "baja",
        ),
        AuditEvidenceItem(
            type="url",
            label="Estado del link",
            value=url_health.status,
            severity="alta" if url_health.is_disconnected else "baja",
        ),
        AuditEvidenceItem(
            type="url",
            label="Tipo de contenido URL",
            value=f"{url_content_classification.content_kind} / noticia: {'si' if url_content_classification.is_news else 'no'}",
            severity="media" if not url_content_classification.is_news else "baja",
        ),
        AuditEvidenceItem(
            type="url",
            label="Reporte tecnico URL",
            value=f"{url_technical_report.operational_status}: {url_technical_report.summary}",
            severity="baja" if url_technical_report.operational_status == "confiable" else "media",
        ),
        AuditEvidenceItem(
            type="risk",
            label="Confiabilidad de noticia",
            value=f"{news_reliability_assessment.level} / {news_reliability_assessment.score}",
            severity="baja" if news_reliability_assessment.score >= 75 else "media",
        ),
        AuditEvidenceItem(
            type="risk",
            label="Impacto de genero",
            value=f"{gender_impact_assessment.status_label} / {gender_impact_assessment.score}",
            severity=(
                "alta"
                if gender_impact_assessment.status == "alerta_impacto_genero"
                else "baja"
                if gender_impact_assessment.status == "sin_senales_relevantes"
                else "media"
            ),
        ),
        AuditEvidenceItem(
            type="related_news",
            label="Noticias relacionadas encontradas",
            value=f"{related_count} ({cross_source_check.coverage_status})",
            severity="media" if related_count == 0 else "baja",
        ),
        AuditEvidenceItem(
            type="risk",
            label="Calidad del articulo",
            value=str(content_quality.quality_score),
            severity="alta" if content_quality.quality_score < 50 else "media",
        ),
        AuditEvidenceItem(
            type="risk",
            label="Contexto compacto LLM",
            value=f"{llm_compact_context.compact_text_chars}/{llm_compact_context.original_text_chars} chars; ~{llm_compact_context.estimated_tokens} tokens",
            severity="baja",
        ),
        AuditEvidenceItem(
            type="risk",
            label="Ejecucion LLM",
            value=f"{llm_execution.provider} / {llm_execution.model or 'sin modelo'} / {llm_execution.status}",
            severity="baja" if llm_execution.status == "used" else "media",
        ),
    ]
    for signal in url_risk_signals[:3]:
        evidence_items.append(
            AuditEvidenceItem(
                type="url",
                label=signal.signal,
                value=signal.explanation,
                severity=signal.severity,
            )
        )
    for gap in analysis.information_gaps[:3]:
        evidence_items.append(
            AuditEvidenceItem(
                type="gap",
                label=gap.missing_item,
                value=gap.why_it_matters,
                severity="alta" if gap.priority == "alta" else "media",
            )
        )
    for claim in verifiable_claims[:3]:
        evidence_items.append(
            AuditEvidenceItem(
                type="claim",
                label=claim.type,
                value=claim.claim,
                severity="media",
            )
        )

    priority = "alta" if analysis.credibility.risk_level in {"alto", "critico"} or content_quality.quality_score < 50 else "media"
    return AuditMetadata(
        ready_for_audit=True,
        priority=priority,
        evidence_summary=(
            f"Fuente: {source_classification.communication_type}. "
            f"Plataforma: {editorial_metadata.platform}. "
            f"Eje: {editorial_metadata.thematic_axis}. "
            f"Relevancia: {information_relevance.relation_type}. "
            f"Link: {url_health.status}. "
            f"Tipo URL: {url_content_classification.content_kind}. "
            f"URL tecnica: {url_technical_report.operational_status}. "
            f"Confiabilidad noticia: {news_reliability_assessment.level}/{news_reliability_assessment.score}. "
            f"Impacto genero: {gender_impact_assessment.status_label}. "
            f"Relacionadas: {related_count}. "
            f"Calidad: {content_quality.quality_score}. "
            f"LLM compacto: ~{llm_compact_context.estimated_tokens} tokens. "
            f"LLM: {llm_execution.provider}/{llm_execution.status}. "
            f"Riesgo: {analysis.credibility.risk_level}."
        ),
        evidence_items=evidence_items,
        presentation_blocks=[
            {
                "title": "Resumen del analisis",
                "bullets": [analysis.summary, analysis.recommendation],
            },
            {
                "title": "Recomendaciones para revisar",
                "items": _build_review_recommendations(
                    analysis,
                    url_health,
                    related_count,
                    source_classification,
                    cross_source_check,
                    url_risk_signals,
                    verifiable_claims,
                ),
            },
            {
                "title": "Puntos para verificar",
                "bullets": [claim.claim for claim in verifiable_claims[:4]],
            }
        ],
    )


def _build_review_recommendations(
    analysis,
    url_health,
    related_count: int,
    source_classification,
    cross_source_check,
    url_risk_signals,
    verifiable_claims,
) -> list[dict]:
    recommendations: list[dict] = []

    for gap in analysis.information_gaps[:4]:
        recommendations.append(
            {
                "title": gap.missing_item,
                "action": gap.suggested_verification,
                "reason": gap.why_it_matters,
                "priority": gap.priority,
                "source": "llm_information_gap",
            }
        )

    if analysis.credibility.risk_level in {"alto", "critico"}:
        recommendations.insert(
            0,
            {
                "title": "Riesgo alto en esta noticia",
                "action": "No publicar ni compartir como contenido confirmado hasta contrastar la evidencia central.",
                "reason": analysis.credibility.explanation,
                "priority": "alta",
                "source": "credibility_risk",
            },
        )

    if url_health.is_disconnected:
        recommendations.insert(
            0,
            {
                "title": "URL no disponible",
                "action": "Verificar el enlace original, conservar evidencia de archivo o solicitar una fuente trazable.",
                "reason": "El enlace no esta activo, por lo que baja la trazabilidad de la noticia.",
                "priority": "alta",
                "source": "url_health",
            },
        )

    if related_count == 0 and cross_source_check.coverage_status in {"no_related_coverage", "not_checked"}:
        recommendations.append(
            {
                "title": "Sin cobertura relacionada suficiente",
                "action": "Buscar manualmente cobertura del mismo hecho en medios registrados, fuentes oficiales o verificadores.",
                "reason": "No hay contraste externo suficiente para contextualizar la informacion.",
                "priority": "media",
                "source": "related_news",
            }
        )

    if not source_classification.is_radar_media and source_classification.registry_status == "unknown":
        recommendations.append(
            {
                "title": "Fuente no registrada en la base interna",
                "action": "Revisar autor, trayectoria del medio, datos de contacto y cobertura de otros medios antes de usarla como evidencia.",
                "reason": "El origen no esta clasificado como medio registrado o verificador dentro del radar.",
                "priority": "media",
                "source": "source_registry",
            }
        )

    high_url_signal = next((signal for signal in url_risk_signals if signal.severity == "alta"), None)
    if high_url_signal:
        recommendations.append(
            {
                "title": high_url_signal.signal,
                "action": "Revisar el enlace y el dominio final antes de usar la noticia como evidencia.",
                "reason": high_url_signal.explanation,
                "priority": "alta",
                "source": "url_risk",
            }
        )

    if verifiable_claims and len(recommendations) < 5:
        recommendations.append(
            {
                "title": "Afirmaciones verificables detectadas",
                "action": "Contrastar las afirmaciones principales con documentos, bases oficiales o declaraciones completas.",
                "reason": "La noticia contiene datos o hechos que pueden ser comprobados con evidencia externa.",
                "priority": "media",
                "source": "claims",
            }
        )

    seen: set[str] = set()
    unique = []
    for item in recommendations:
        key = f"{item['title']}|{item['action']}".lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:5]
