from fastapi import APIRouter, HTTPException, Query

from app.core.security import UnsafeUrlError, validate_public_http_url
from app.schemas.news import AnalysisListItem, AnalyzeRequest, AnalyzeResponse, KuybotRequest, KuybotResponse, SourceInput
from app.services.ai_analyzer import analyze_article
from app.services.article_extractor import ExtractionError, extract_article
from app.services.article_fetcher import FetchError, fetch_html
from app.services.claims_extractor import extract_verifiable_claims
from app.services.claim_contrast import build_claim_contrasts
from app.services.content_quality import evaluate_content_quality
from app.services.content_attribution import build_content_attribution
from app.services.cross_source import build_cross_source_check
from app.services.editorial_metadata import build_editorial_metadata
from app.services.firestore_store import new_analysis_id, now_utc, store
from app.services.information_relevance import classify_information_relevance
from app.services.kuybot import ask_kuybot
from app.services.related_search import search_related_news
from app.services.source_classifier import classify_source
from app.services.source_verification import build_source_verification
from app.services.url_risk import evaluate_url_risk
from app.services.url_trust import build_url_trust_assessment


router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_news(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        safe_url = validate_public_http_url(str(request.url))
        fetched = await fetch_html(safe_url)
        article = extract_article(fetched.final_url, fetched.html)
        source_classification = classify_source(safe_url, article.source_domain)
        content_attribution = build_content_attribution(safe_url, article, source_classification)
        content_quality = evaluate_content_quality(article)
        analysis = await analyze_article(article)
        editorial_metadata = build_editorial_metadata(request, article, source_classification, analysis, content_attribution)
        information_relevance = classify_information_relevance(article, analysis)
        related_news = await search_related_news(analysis, fetched.final_url)
        url_risk_signals = evaluate_url_risk(safe_url, fetched.final_url, fetched.url_health)
        url_trust_assessment = build_url_trust_assessment(fetched.url_health, url_risk_signals)
        verifiable_claims = extract_verifiable_claims(article)
        claim_contrasts = build_claim_contrasts(verifiable_claims, related_news)
        cross_source_check = build_cross_source_check(related_news)
        source_verification = build_source_verification(source_classification, content_attribution, cross_source_check)
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FetchError, ExtractionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error analizando noticia: {exc}") from exc

    response = AnalyzeResponse(
        id=new_analysis_id(),
        status="completed",
        created_at=now_utc(),
        updated_at=now_utc(),
        source_input=SourceInput(original_url=safe_url, final_url=fetched.final_url),
        editorial_metadata=editorial_metadata,
        content_attribution=content_attribution,
        source_verification=source_verification,
        information_relevance=information_relevance,
        url_health=fetched.url_health,
        url_trust_assessment=url_trust_assessment,
        url_risk_signals=url_risk_signals,
        article=article,
        content_quality=content_quality,
        source_classification=source_classification,
        analysis=analysis,
        verifiable_claims=verifiable_claims,
        claim_contrasts=claim_contrasts,
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
            cross_source_check,
        ),
        related_news=related_news,
    )
    return await store.save_analysis(response)


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str) -> dict:
    result = await store.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analisis no encontrado.")
    return result


@router.post("/kuybot", response_model=KuybotResponse)
async def ask_news_kuybot(request: KuybotRequest) -> KuybotResponse:
    try:
        return await ask_kuybot(request.question, request.news, [message.model_dump(mode="json") for message in request.history])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generando respuesta de Kuybot: {exc}") from exc


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
    cross_source_check,
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
            f"Relacionadas: {related_count}. "
            f"Calidad: {content_quality.quality_score}. "
            f"Riesgo: {analysis.credibility.risk_level}."
        ),
        evidence_items=evidence_items,
        presentation_blocks=[
            {
                "title": "Resumen del analisis",
                "bullets": [analysis.summary, analysis.recommendation],
            },
            {
                "title": "Puntos para verificar",
                "bullets": [claim.claim for claim in verifiable_claims[:4]],
            }
        ],
    )
