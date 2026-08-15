from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    force_refresh: bool = False
    platform: Literal["sitio_web", "red_social"] | None = None
    publisher_type: Literal[
        "usuario_cuenta_personal",
        "institucion_publica",
        "institucion_privada",
        "medio_comunicacion",
        "otro",
        "desconocido",
    ] | None = None
    publication_date: str | None = None
    thematic_axis: str | None = None


class SourceInput(BaseModel):
    type: Literal["url"] = "url"
    original_url: str
    final_url: str | None = None
    submitted_title: str | None = None


class EditorialMetadata(BaseModel):
    platform: Literal["sitio_web", "red_social", "desconocido"]
    publisher_type: Literal[
        "usuario_cuenta_personal",
        "institucion_publica",
        "institucion_privada",
        "medio_comunicacion",
        "otro",
        "desconocido",
    ]
    publication_date: str | None = None
    thematic_axis: str | None = None
    thematic_tags: list[str] = Field(default_factory=list)
    inferred: bool = True
    confidence: float = Field(ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class ContentAttribution(BaseModel):
    platform_name: str
    platform_type: Literal["sitio_web", "red_social", "desconocido"]
    shared_by_account: str | None = None
    shared_by_display_name: str | None = None
    publisher_name: str | None = None
    publisher_handle: str | None = None
    publisher_type: Literal[
        "usuario_cuenta_personal",
        "institucion_publica",
        "institucion_privada",
        "medio_comunicacion",
        "otro",
        "desconocido",
    ] = "desconocido"
    source_domain: str | None = None
    explanation: str


class SourceVerification(BaseModel):
    status: Literal[
        "radar_media",
        "registered_media",
        "ifcn_verified",
        "unregistered_source",
        "social_account",
        "unknown",
    ]
    source_name: str | None = None
    matched_domain: str | None = None
    verification_network: str | None = None
    needs_additional_validation: bool
    recommendation: str
    reasons: list[str] = Field(default_factory=list)


class InformationRelevance(BaseModel):
    is_relevant: bool
    relevance_score: int = Field(ge=0, le=100)
    domain: Literal["electoral", "no_electoral", "indeterminado"]
    definition_applied: str
    subtopics: list[str] = Field(default_factory=list)
    relation_type: Literal[
        "directa",
        "indirecta",
        "contextual",
        "no_relacionada",
        "indeterminada",
    ]
    reasons: list[str] = Field(default_factory=list)
    how_it_relates: str
    non_relevant_reason: str | None = None


class UrlHealth(BaseModel):
    status: Literal["active", "redirected", "disconnected", "blocked", "error"]
    http_status: int | None = None
    is_reachable: bool
    is_disconnected: bool
    redirect_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class UrlTrustAssessment(BaseModel):
    is_technically_trustworthy: bool
    level: Literal["confiable", "precaucion", "riesgosa", "indeterminada"]
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    scope: Literal["url_only"] = "url_only"


class UrlContentClassification(BaseModel):
    is_news: bool
    content_kind: Literal[
        "noticia",
        "publicacion_red_social",
        "video_audio",
        "otro",
        "indeterminado",
    ]
    confidence: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class NewsReliabilityAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["alta", "media", "baja", "indeterminada"]
    is_reliable_source_context: bool
    explanation: str
    factors: list[str] = Field(default_factory=list)
    scope: Literal["fuente_contenido_cobertura"] = "fuente_contenido_cobertura"


class UrlRiskSignal(BaseModel):
    signal: str
    severity: Literal["baja", "media", "alta"]
    explanation: str


class UrlTechnicalReport(BaseModel):
    original_domain: str | None = None
    final_domain: str | None = None
    uses_https: bool
    redirected_to_different_domain: bool = False
    redirect_count: int = 0
    http_status: int | None = None
    is_reachable: bool
    is_registered_source: bool
    source_name: str | None = None
    content_kind: str
    risk_signal_count: int = 0
    high_or_medium_risk_count: int = 0
    operational_status: Literal["confiable", "precaucion", "requiere_revision", "indeterminado"]
    summary: str
    recommendations: list[str] = Field(default_factory=list)


class ExtractedArticle(BaseModel):
    url: str
    source_domain: str
    title: str | None = None
    author: str | None = None
    published_at: str | None = None
    language: str | None = None
    image_url: str | None = None
    text: str


class SourceClassification(BaseModel):
    is_radar_media: bool
    communication_type: Literal[
        "medio_radar",
        "medio_no_radar",
        "red_social",
        "blog",
        "gobierno",
        "institucion",
        "empresa",
        "ong",
        "plataforma_video",
        "otro",
        "desconocido",
    ]
    source_name: str | None = None
    matched_domain: str | None = None
    matched_handle: str | None = None
    registry_category: str | None = None
    editorial_alignment: str | None = None
    platform: str | None = None
    verification_network: str | None = None
    confidence: float = Field(ge=0, le=1)
    explanation: str

    @property
    def registry_status(self) -> str:
        # Backward-compatible status used by legacy recommendation logic.
        if self.is_radar_media:
            return "radar"
        if self.registry_category or self.source_name:
            return "registered"
        return "unknown"


class SentimentAnalysis(BaseModel):
    label: Literal["positivo", "neutral", "negativo", "mixto"]
    score: float = Field(ge=0, le=1)


class BiasAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    direction: str
    explanation: str


class ClickbaitAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)


class CredibilityAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    risk_level: Literal["bajo", "medio", "alto", "critico"]
    explanation: str


class InformationGap(BaseModel):
    missing_item: str
    why_it_matters: str
    suggested_verification: str
    priority: Literal["baja", "media", "alta"]


class EntitySet(BaseModel):
    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)


class NewsAnalysis(BaseModel):
    summary: str
    topic: str
    category: str
    main_claims: list[str] = Field(default_factory=list)
    entities: EntitySet = Field(default_factory=EntitySet)
    keywords: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    sentiment: SentimentAnalysis
    bias_analysis: BiasAnalysis
    manipulation_signals: list[str] = Field(default_factory=list)
    clickbait: ClickbaitAnalysis
    credibility: CredibilityAnalysis
    information_gaps: list[InformationGap] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    recommendation: str


class RelatedNewsItem(BaseModel):
    title: str
    url: str
    source: str | None = None
    source_name: str | None = None
    source_type: str | None = None
    source_registry_status: str | None = None
    source_confidence_score: int | None = Field(default=None, ge=0, le=100)
    source_veracity_score: int | None = Field(default=None, ge=0, le=100)
    relation_score: int | None = Field(default=None, ge=0, le=100)
    relation_label: str | None = None
    snippet: str | None = None
    published_at: str | None = None
    relation_reason: str | None = None


class ContentQuality(BaseModel):
    has_author: bool
    has_date: bool
    text_length: int
    has_sources: bool
    title_body_overlap_score: float = Field(ge=0, le=1)
    quality_score: int = Field(ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)


class VerifiableClaim(BaseModel):
    claim: str
    type: Literal["estadistica", "evento", "cita", "acusacion", "fecha", "lugar", "otro"]
    entities: list[str] = Field(default_factory=list)
    needs_external_verification: bool = True


class LlmCompactContext(BaseModel):
    title: str | None = None
    source_domain: str | None = None
    published_at: str | None = None
    keywords: list[str] = Field(default_factory=list)
    top_sentences: list[str] = Field(default_factory=list)
    candidate_claims: list[str] = Field(default_factory=list)
    original_text_chars: int = 0
    compact_text_chars: int = 0
    estimated_tokens: int = 0
    compression_ratio: float = Field(ge=0, le=1)


class LlmExecutionMetadata(BaseModel):
    provider: Literal["groq", "openai", "heuristic"]
    model: str | None = None
    status: Literal["used", "fallback", "disabled", "failed"]
    error: str | None = None


class ClaimContrast(BaseModel):
    timestamp: str | None = None
    claim: str
    status: Literal[
        "coincide_con_fuentes",
        "requiere_contexto",
        "informacion_a_contrastar",
        "sin_respaldo_suficiente",
        "no_verificable",
    ]
    status_label: str
    explanation: str
    sources_consulted: list[str] = Field(default_factory=list)
    evidence_url: str | None = None


class GenderImpactSignal(BaseModel):
    signal_type: Literal[
        "estereotipos_genero",
        "descalificacion_genero",
        "sexualizacion",
        "roles_familiares",
        "lenguaje_degradante",
        "amenazas_intimidacion",
        "contenido_manipulado",
        "hostigamiento_reiterado",
    ]
    label: str
    evidence: str
    severity: Literal["baja", "media", "alta"]


class GenderImpactAssessment(BaseModel):
    status: Literal[
        "sin_senales_relevantes",
        "senales_para_revision",
        "alerta_impacto_genero",
    ]
    status_label: str
    score: int = Field(ge=0, le=100)
    signals: list[GenderImpactSignal] = Field(default_factory=list)
    explanation: str
    requires_specialized_review: bool = False
    scope: Literal["contenido"] = "contenido"


class CrossSourceCheck(BaseModel):
    related_coverage_count: int = 0
    radar_media_coverage_count: int = 0
    independent_sources_count: int = 0
    contradictions_found: bool = False
    coverage_status: Literal[
        "multiple_sources",
        "single_source",
        "no_related_coverage",
        "not_checked",
    ] = "not_checked"
    notes: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["bajo", "medio", "alto", "critico"]
    fraud_or_disinformation_risk: Literal["bajo", "medio", "alto", "critico"]
    reasons: list[str] = Field(default_factory=list)
    cannot_conclude_fraud: bool = True


class AuditEvidenceItem(BaseModel):
    type: Literal["url", "claim", "gap", "related_news", "source", "risk"]
    label: str
    value: str
    severity: Literal["baja", "media", "alta"] = "media"


class AuditMetadata(BaseModel):
    ready_for_audit: bool = True
    priority: Literal["baja", "media", "alta", "critica"] = "media"
    evidence_summary: str
    evidence_items: list[AuditEvidenceItem] = Field(default_factory=list)
    presentation_blocks: list[dict] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    id: str
    user_id: str | None = None
    module: Literal["noticias"] = "noticias"
    content_type: Literal["news_url"] = "news_url"
    visibility: Literal["private", "public", "internal"] = "private"
    status: Literal["processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    source_input: SourceInput
    editorial_metadata: EditorialMetadata
    content_attribution: ContentAttribution
    source_verification: SourceVerification
    information_relevance: InformationRelevance
    url_health: UrlHealth
    url_trust_assessment: UrlTrustAssessment
    url_content_classification: UrlContentClassification
    news_reliability_assessment: NewsReliabilityAssessment
    url_technical_report: UrlTechnicalReport
    url_risk_signals: list[UrlRiskSignal] = Field(default_factory=list)
    article: ExtractedArticle
    content_quality: ContentQuality
    source_classification: SourceClassification
    analysis: NewsAnalysis
    llm_compact_context: LlmCompactContext
    llm_execution: LlmExecutionMetadata
    verifiable_claims: list[VerifiableClaim] = Field(default_factory=list)
    claim_contrasts: list[ClaimContrast] = Field(default_factory=list)
    gender_impact_assessment: GenderImpactAssessment
    cross_source_check: CrossSourceCheck
    risk_assessment: RiskAssessment
    audit: AuditMetadata
    related_news: list[RelatedNewsItem] = Field(default_factory=list)


class AnalysisListItem(BaseModel):
    id: str
    user_id: str | None = None
    module: str | None = None
    content_type: str | None = None
    visibility: str | None = None
    url: str
    title: str | None = None
    source_domain: str | None = None
    communication_type: str | None = None
    is_radar_media: bool | None = None
    topic: str | None = None
    keywords: list[str] = Field(default_factory=list)
    credibility_score: int | None = None
    risk_level: str | None = None
    audit_priority: str | None = None
    created_at: datetime | None = None


class KuybotMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = ""
    sources: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    text: str | None = None

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict):
            role = obj.get("role")
            if role == "bot":
                obj = {**obj, "role": "assistant"}
            if "content" not in obj and "text" in obj:
                obj = {**obj, "content": obj["text"]}
            if "text" not in obj and "content" in obj:
                obj = {**obj, "text": obj["content"]}
        return super().model_validate(obj, *args, **kwargs)


class KuybotRequest(BaseModel):
    question: str
    news: dict | None = None
    history: list[KuybotMessage] = Field(default_factory=list)


class KuybotFactCheckItem(BaseModel):
    text: str | None = None
    claimant: str | None = None
    publisher: str | None = None
    review_date: str | None = None
    url: str | None = None
    language_code: str | None = None


class KuybotResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    fact_check: list[KuybotFactCheckItem] = Field(default_factory=list)
    mode: Literal["gemini", "fallback"] = "fallback"
    status: Literal["ok", "error"] = "ok"
