"""
Firebase Firestore service for saving video/audio analysis results.
Integrates with existing contentAnalyses collection using content_type: "video_audio".
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Optional
import hashlib
from datetime import datetime, timezone
import json
import os

_firebase_app = None
_db = None


def _init_firebase():
    global _firebase_app, _db
    if _firebase_app is not None:
        return _db

    from app.config import settings

    cred_path = settings.firebase_credentials_path
    project_id = settings.firebase_project_id

    if not cred_path or not os.path.exists(cred_path):
        print("⚠️ Firebase credentials not found, skipping Firestore save")
        return None

    try:
        with open(cred_path) as f:
            cred_dict = json.load(f)

        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred, name="video-audio-analyzer")
        _db = firestore.client(app=_firebase_app)
        print(f"✅ Firebase connected: {project_id}")
        return _db
    except Exception as e:
        print(f"⚠️ Firebase init error: {e}")
        return None


def _generate_doc_id(url: str = "", filename: str = "", timestamp: float = 0) -> str:
    """Generate UUID hash without dashes (same format as existing docs)."""
    raw = f"{url or filename or 'upload'}_{timestamp or datetime.now(timezone.utc).timestamp()}"
    return hashlib.md5(raw.encode()).hexdigest()


def save_analysis_to_firestore(analysis_result: Dict, source_metadata: Optional[Dict] = None) -> Optional[str]:
    """
    Save video/audio analysis result to Firestore contentAnalyses collection.

    Args:
        analysis_result: Full analysis result from perform_content_analysis
        source_metadata: Optional metadata about source (URL, channel, title)

    Returns:
        Document ID if saved, None if failed
    """
    db = _init_firebase()
    if db is None:
        return None

    try:
        now = datetime.now(timezone.utc)
        doc_id = _generate_doc_id(
            url=source_metadata.get("source_url", "") if source_metadata else "",
            filename=analysis_result.get("metadata", {}).get("filename", ""),
            timestamp=now.timestamp()
        )

        # Build document matching existing contentAnalyses structure
        doc_data = {
            # Core identity
            "id": doc_id,
            "module": "video_audio",
            "content_type": "video_audio",
            "status": "completed",
            "visibility": "private",
            "user_id": None,

            # Timestamps
            "created_at": now,
            "updated_at": now,

            # Source info
            "source_input": {
                "source_url": source_metadata.get("source_url", "") if source_metadata else "",
                "platform": source_metadata.get("platform", "") if source_metadata else "",
                "channel": source_metadata.get("channel", "") if source_metadata else "",
                "title": source_metadata.get("title", "") if source_metadata else "",
                "thumbnail": source_metadata.get("thumbnail", "") if source_metadata else "",
                "filename": analysis_result.get("metadata", {}).get("filename", ""),
            },

            # Article/media metadata
            "article": {
                "title": source_metadata.get("title", "") if source_metadata else analysis_result.get("metadata", {}).get("filename", "contenido analizado"),
                "language": analysis_result.get("content_analysis", {}).get("transcription", {}).get("language", "es"),
                "duration": analysis_result.get("metadata", {}).get("duration", 0),
                "format": analysis_result.get("metadata", {}).get("format", "unknown"),
                "resolution": analysis_result.get("metadata", {}).get("resolution", None),
                "fps": analysis_result.get("metadata", {}).get("fps", None),
                "size": analysis_result.get("metadata", {}).get("size", None),
            },

            # AI detection (deepfake)
            "ai_detection": {
                "is_ai_generated": analysis_result.get("is_ai_generated", False),
                "is_manipulated": analysis_result.get("is_manipulated", False),
                "confidence": analysis_result.get("confidence", 0.0),
                "analysis_type": analysis_result.get("analysis_type", "video"),
                "video_details": _serialize_dict(analysis_result.get("video_details")),
                "audio_details": _serialize_dict(analysis_result.get("audio_details")),
            },

            # LLM analysis
            "llm_execution": {
                "provider": "groq",
                "model": _safe_llm(analysis_result).get("model_used", "llama-3.3-70b-versatile"),
                "error": None,
                "status": "used",
                "tokens_used": _safe_llm(analysis_result).get("tokens_used", 0),
            },

            # LLM compact context (verdict, summary, claims)
            "llm_compact_context": {
                "veredicto": _safe_llm(analysis_result).get("veredicto", ""),
                "confianza": _safe_llm(analysis_result).get("confianza", 0),
                "resumen": _safe_llm(analysis_result).get("resumen", ""),
                "tema_principal": _safe_llm(analysis_result).get("tema_principal", ""),
                "contexto_politico": _safe_llm(analysis_result).get("contexto_politico", ""),
                "coincide_con_fuentes": _safe_llm(analysis_result).get("coincide_con_fuentes", False),
                "afirmaciones_clave": _safe_llm(analysis_result).get("afirmaciones_clave", []),
                "observaciones": _safe_llm(analysis_result).get("observaciones", ""),
            },

            # Relevance
            "information_relevance": {
                "is_relevant": _safe_llm(analysis_result).get("is_relevant", True),
                "relevance_category": _safe_llm(analysis_result).get("relevance_category", ""),
                "non_relevant_reason": None if _safe_llm(analysis_result).get("is_relevant", True) else "Contenido no aplicable para verificacion",
            },

            # Verifiable claims from transcription
            "verifiable_claims": [
                {
                    "text": claim,
                    "type": "declaracion",
                    "source": "transcription",
                    "needs_external_verification": True,
                }
                for claim in _safe_llm(analysis_result).get("afirmaciones_clave", [])
            ],

            # Cross-source check (web context)
            "cross_source_check": {
                "related_coverage_count": analysis_result.get("content_analysis", {}).get("web_context", {}).get("total_articles_found", 0),
                "independent_sources_count": len([
                    a for a in analysis_result.get("content_analysis", {}).get("web_context", {}).get("cross_reference", {}).get("matching_articles", [])
                    if a.get("is_reliable")
                ]),
                "matched_sources": _serialize_list(
                    analysis_result.get("content_analysis", {}).get("web_context", {}).get("cross_reference", {}).get("matching_articles", [])
                ),
            },

            # Source verification
            "source_verification": {
                "recommendation": _build_source_recommendation(analysis_result),
                "sources_found": analysis_result.get("content_analysis", {}).get("web_context", {}).get("total_articles_found", 0),
            },

            # Risk assessment
            "risk_assessment": _build_risk_assessment(analysis_result),

            # Editorial metadata
            "editorial_metadata": {
                "publisher_type": "plataforma_video" if analysis_result.get("analysis_type") == "video" else "plataforma_audio",
                "platform": source_metadata.get("platform", "upload") if source_metadata else "upload",
                "thematic_tags": [_safe_llm(analysis_result).get("tema_principal", "")] if _safe_llm(analysis_result).get("tema_principal") else [],
                "inferred": True,
            },

            # Audit
            "audit": {
                "priority": "alta" if analysis_result.get("is_ai_generated") else "media",
                "ready_for_audit": True,
                "evidence_summary": _build_evidence_summary(analysis_result),
            },

            # Processing info
            "processing_time": analysis_result.get("processing_time", 0),
        }

        # Save to Firestore
        doc_ref = db.collection("contentAnalyses").document(doc_id)
        doc_ref.set(doc_data)

        # Save transcript in subcollection
        transcription = analysis_result.get("content_analysis", {}).get("transcription", {})
        if transcription and transcription.get("text"):
            doc_ref.collection("transcripts").document("full").set({
                "text": transcription.get("text", ""),
                "language": transcription.get("language", "es"),
                "segments": _serialize_list(transcription.get("segments", [])),
                "segment_verifications": _serialize_list(transcription.get("segment_verifications", [])),
                "created_at": now,
            })

        # Save media assets in subcollection
        if source_metadata and source_metadata.get("source_url"):
            doc_ref.collection("mediaAssets").document("source").set({
                "url": source_metadata.get("source_url", ""),
                "platform": source_metadata.get("platform", ""),
                "thumbnail": source_metadata.get("thumbnail", ""),
                "channel": source_metadata.get("channel", ""),
                "title": source_metadata.get("title", ""),
                "created_at": now,
            })

        # Save web sources in subcollection
        web_articles = analysis_result.get("content_analysis", {}).get("web_context", {}).get("articles", [])
        if web_articles:
            for idx, article in enumerate(web_articles[:8]):
                doc_ref.collection("knowledgeSources").document(f"source_{idx}").set({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", ""),
                    "snippet": article.get("snippet", ""),
                    "date": article.get("date", ""),
                    "is_reliable": article.get("is_reliable", False),
                    "reliable_name": article.get("reliable_name"),
                    "created_at": now,
                })

        print(f"✅ Analysis saved to Firestore: contentAnalyses/{doc_id}")
        return doc_id

    except Exception as e:
        print(f"⚠️ Firestore save error: {e}")
        return None


def _serialize_dict(obj) -> Optional[Dict]:
    """Serialize object to dict, handling None and non-serializable values."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    return obj


def _serialize_list(obj) -> list:
    """Serialize list, handling non-serializable values."""
    if obj is None:
        return []
    if isinstance(obj, list):
        return [_serialize_value(v) for v in obj]
    return []


def _serialize_value(v):
    """Handle Firestore-incompatible values."""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_serialize_value(item) for item in v]
    return str(v)


def _safe_llm(analysis_result: Dict) -> Dict:
    """Get llm_analysis as dict, handling None safely."""
    llm = analysis_result.get("content_analysis", {}).get("llm_analysis")
    return llm if isinstance(llm, dict) else {}


def _build_source_recommendation(analysis_result: Dict) -> str:
    """Build source recommendation text based on analysis."""
    llm = _safe_llm(analysis_result)
    web = analysis_result.get("content_analysis", {}).get("web_context", {})
    articles = web.get("articles", [])
    reliable = [a for a in articles if a.get("is_reliable")]

    if not articles:
        return "No se encontraron fuentes web. Analisis basado en transcripcion y modelo LLM."
    if reliable:
        return f"Se encontraron {len(reliable)} fuente(s) confiable(s). Veredicto: {llm.get('veredicto', 'N/A')}."
    return f"Se encontraron {len(articles)} fuente(s) pero ninguna en lista radar. Veredicto: {llm.get('veredicto', 'N/A')}."


def _build_risk_assessment(analysis_result: Dict) -> Dict:
    """Build risk assessment from analysis."""
    llm = _safe_llm(analysis_result)
    is_ai = analysis_result.get("is_ai_generated", False)
    is_manipulated = analysis_result.get("is_manipulated", False)

    reasons = []
    score = 0

    if is_ai:
        reasons.append("Contenido presenta patrones de generacion artificial (deepfake).")
        score += 60
    if is_manipulated:
        reasons.append("Se detectaron anomalias de manipulacion.")
        score += 30

    verdict = llm.get("veredicto", "")
    if verdict == "FALSO":
        score += 40
        reasons.append("Veredicto LLM: FALSO.")
    elif verdict == "ENGAÑOSO":
        score += 25
        reasons.append("Veredicto LLM: ENGAÑOSO.")
    elif verdict == "MIXTO":
        score += 15
        reasons.append("Veredicto LLM: MIXTO.")

    if not reasons:
        reasons.append("Sin senales de riesgo detectadas.")

    level = "alto" if score >= 60 else "medio" if score >= 30 else "bajo"

    return {
        "reasons": reasons,
        "score": min(score, 100),
        "level": level,
    }


def _build_evidence_summary(analysis_result: Dict) -> str:
    """Build evidence summary for audit."""
    llm = _safe_llm(analysis_result)
    is_ai = analysis_result.get("is_ai_generated", False)
    web = analysis_result.get("content_analysis", {}).get("web_context", {})
    articles_count = web.get("total_articles_found", 0)

    parts = []
    parts.append(f"Tipo: {analysis_result.get('analysis_type', 'video')}")
    parts.append(f"IA detectada: {'si' if is_ai else 'no'}")
    parts.append(f"Veredicto LLM: {llm.get('veredicto', 'N/A')}")
    parts.append(f"Fuentes web: {articles_count}")
    return ". ".join(parts)
