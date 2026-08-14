from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import settings
from app.schemas.news import AnalysisListItem, AnalyzeResponse


class NewsStore:
    def __init__(self) -> None:
        self._client = None
        self._memory: dict[str, dict] = {}
        self._init_firestore()

    def _init_firestore(self) -> None:
        if not settings.firebase_project_id and not settings.firebase_credentials_path:
            return

        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                if settings.firebase_credentials_path:
                    cred = credentials.Certificate(settings.firebase_credentials_path)
                    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                else:
                    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
            self._client = firestore.client()
        except Exception:
            self._client = None

    async def save_analysis(self, response: AnalyzeResponse) -> AnalyzeResponse:
        data = response.model_dump(mode="json")
        if self._client:
            self._client.collection(settings.firestore_collection).document(response.id).set(data)
        else:
            self._memory[response.id] = data
        return response

    async def get_analysis(self, analysis_id: str) -> dict | None:
        if self._client:
            doc = self._client.collection(settings.firestore_collection).document(analysis_id).get()
            return doc.to_dict() if doc.exists else None
        return self._memory.get(analysis_id)

    async def list_analyses(self, limit: int = 20) -> list[AnalysisListItem]:
        if self._client:
            docs = (
                self._client.collection(settings.firestore_collection)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            rows = [doc.to_dict() | {"id": doc.id} for doc in docs]
        else:
            rows = sorted(self._memory.values(), key=lambda item: item.get("created_at", ""), reverse=True)[:limit]

        return [_to_list_item(row) for row in rows]


def new_analysis_id() -> str:
    return uuid4().hex


def now_utc() -> datetime:
    return datetime.now(UTC)


def _to_list_item(row: dict) -> AnalysisListItem:
    article = row.get("article", {})
    analysis = row.get("analysis", {})
    source_classification = row.get("source_classification", {})
    editorial_metadata = row.get("editorial_metadata", {})
    information_relevance = row.get("information_relevance", {})
    credibility = analysis.get("credibility", {})
    audit = row.get("audit", {})
    return AnalysisListItem(
        id=row.get("id"),
        user_id=row.get("user_id"),
        module=row.get("module"),
        content_type=row.get("content_type"),
        visibility=row.get("visibility"),
        url=article.get("url", ""),
        title=article.get("title"),
        source_domain=article.get("source_domain"),
        communication_type=source_classification.get("communication_type"),
        is_radar_media=source_classification.get("is_radar_media"),
        topic=editorial_metadata.get("thematic_axis") or ", ".join(information_relevance.get("subtopics", [])) or analysis.get("topic"),
        keywords=analysis.get("keywords", []),
        credibility_score=credibility.get("score"),
        risk_level=credibility.get("risk_level"),
        audit_priority=audit.get("priority"),
        created_at=row.get("created_at"),
    )


store = NewsStore()
