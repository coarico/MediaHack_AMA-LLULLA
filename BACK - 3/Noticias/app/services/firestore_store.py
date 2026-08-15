import asyncio
import base64
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import re
import time
from urllib.parse import quote, urlencode
from urllib.request import Request as UrlRequest, urlopen
from uuid import uuid4

from app.core.config import settings
from app.schemas.news import AnalysisListItem, AnalyzeResponse


logger = logging.getLogger(__name__)
FIRESTORE_READ_TIMEOUT_SECONDS = 3
FIRESTORE_WRITE_TIMEOUT_SECONDS = 6


class NewsStore:
    def __init__(self) -> None:
        self._client = None
        self._rest_credentials = None
        self._rest_token: str | None = None
        self._rest_token_expires_at = 0
        self._memory: dict[str, dict] = {}
        self._init_firestore()

    def _init_firestore(self) -> None:
        if not settings.firebase_project_id and not settings.firebase_credentials_path:
            return

        try:
            if settings.firestore_transport == "rest":
                self._init_firestore_rest()
                return

            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                if settings.firebase_credentials_path:
                    cred = credentials.Certificate(_resolve_credentials_path(settings.firebase_credentials_path))
                    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                else:
                    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
            self._client = firestore.client()
            logger.info("Firestore conectado: project_id=%s collection=%s", settings.firebase_project_id, settings.firestore_collection)
        except Exception as exc:
            self._client = None
            self._rest_credentials = None
            logger.warning("Firestore no disponible, usando memoria local: %s", exc)

    def _init_firestore_rest(self) -> None:
        if not settings.firebase_project_id or not settings.firebase_credentials_path:
            return
        from google.oauth2 import service_account

        self._rest_credentials = service_account.Credentials.from_service_account_file(
            _resolve_credentials_path(settings.firebase_credentials_path),
            scopes=[
                "https://www.googleapis.com/auth/datastore",
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        )
        logger.info("Firestore REST configurado: project_id=%s collection=%s", settings.firebase_project_id, settings.firestore_collection)

    async def save_analysis(self, response: AnalyzeResponse) -> AnalyzeResponse:
        data = response.model_dump(mode="json")
        self._memory[response.id] = data
        if self._rest_credentials:
            await self._safe_remote_write(response.id, data)
        elif self._client:
            await self._safe_remote_write(response.id, data)
        return response

    async def update_analysis(self, response: AnalyzeResponse) -> AnalyzeResponse:
        data = response.model_dump(mode="json")
        self._memory[response.id] = data
        if self._rest_credentials:
            await self._safe_remote_write(response.id, data)
        elif self._client:
            await self._safe_remote_write(response.id, data, merge=True)
        return response

    async def get_analysis(self, analysis_id: str) -> dict | None:
        cached = self._memory.get(analysis_id)
        if self._rest_credentials:
            data = await self._safe_remote_get(analysis_id)
            if data:
                self._memory[analysis_id] = data
                return data
            return cached
        if self._client:
            data = await self._safe_remote_get(analysis_id)
            if data:
                self._memory[analysis_id] = data
                return data
            return cached
        return cached

    async def list_analyses(self, limit: int = 20) -> list[AnalysisListItem]:
        if self._rest_credentials:
            rows = await self._safe_remote_list(limit)
        elif self._client:
            rows = await self._safe_remote_list(limit)
        else:
            rows = []

        if not rows:
            rows = sorted(self._memory.values(), key=lambda item: item.get("created_at", ""), reverse=True)[:limit]

        return [_to_list_item(row) for row in rows]

    async def _safe_remote_write(self, document_id: str, data: dict, merge: bool = False) -> None:
        try:
            await asyncio.wait_for(
                asyncio.to_thread(self._remote_write, document_id, data, merge),
                timeout=FIRESTORE_WRITE_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.warning("Firestore write omitido, usando cache local: %s", exc)

    async def _safe_remote_get(self, document_id: str) -> dict | None:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._remote_get, document_id),
                timeout=FIRESTORE_READ_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.warning("Firestore get omitido, usando cache local: %s", exc)
            return None

    async def _safe_remote_list(self, limit: int) -> list[dict]:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._remote_list, limit),
                timeout=FIRESTORE_READ_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.warning("Firestore list omitido, usando cache local: %s", exc)
            return []

    def _remote_write(self, document_id: str, data: dict, merge: bool = False) -> None:
        if self._rest_credentials:
            self._rest_write(document_id, data)
        elif self._client:
            self._client.collection(settings.firestore_collection).document(document_id).set(data, merge=merge)

    def _remote_get(self, document_id: str) -> dict | None:
        if self._rest_credentials:
            return self._rest_get(document_id)
        if self._client:
            doc = self._client.collection(settings.firestore_collection).document(document_id).get()
            return doc.to_dict() if doc.exists else None
        return None

    def _remote_list(self, limit: int) -> list[dict]:
        if self._rest_credentials:
            return self._rest_list(limit)
        if self._client:
            docs = (
                self._client.collection(settings.firestore_collection)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [doc.to_dict() | {"id": doc.id} for doc in docs]
        return []

    def _rest_write(self, document_id: str, data: dict) -> None:
        url = f"{_firestore_document_base_url()}/{quote(document_id, safe='')}"
        payload = json.dumps({"fields": _to_firestore_fields(data)}).encode("utf-8")
        request = UrlRequest(
            url,
            data=payload,
            method="PATCH",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=15) as response:
            response.read()

    def _rest_get(self, document_id: str) -> dict | None:
        url = f"{_firestore_document_base_url()}/{quote(document_id, safe='')}"
        request = UrlRequest(url, headers={"Authorization": f"Bearer {self._access_token()}"})
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None
        return _from_firestore_fields(payload.get("fields", {}))

    def _rest_list(self, limit: int) -> list[dict]:
        query = urlencode({"pageSize": limit, "orderBy": "created_at desc"})
        url = f"{_firestore_document_base_url()}?{query}"
        request = UrlRequest(url, headers={"Authorization": f"Bearer {self._access_token()}"})
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []
        rows = []
        for document in payload.get("documents", []):
            row = _from_firestore_fields(document.get("fields", {}))
            row["id"] = document.get("name", "").rsplit("/", 1)[-1]
            rows.append(row)
        return rows

    def _access_token(self) -> str:
        now = int(time.time())
        if self._rest_token and now < self._rest_token_expires_at - 60:
            return self._rest_token

        assertion = _build_service_account_assertion(self._rest_credentials, now)
        payload = urlencode(
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            }
        ).encode("utf-8")
        request = UrlRequest(
            _credentials_token_uri(self._rest_credentials),
            data=payload,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=15) as response:
            token_payload = json.loads(response.read().decode("utf-8"))

        self._rest_token = token_payload["access_token"]
        self._rest_token_expires_at = now + int(token_payload.get("expires_in", 3600))
        return self._rest_token


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


def _resolve_credentials_path(credentials_path: str) -> str:
    path = Path(credentials_path)
    if path.is_absolute():
        return str(path)
    backend_root = Path(__file__).resolve().parents[2]
    return str((backend_root / path).resolve())


def _firestore_document_base_url() -> str:
    project_id = quote(settings.firebase_project_id or "", safe="")
    collection = quote(settings.firestore_collection, safe="")
    return f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{collection}"


def _build_service_account_assertion(credentials, now: int) -> str:
    token_uri = _credentials_token_uri(credentials)
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": credentials.service_account_email,
        "scope": "https://www.googleapis.com/auth/datastore https://www.googleapis.com/auth/cloud-platform",
        "aud": token_uri,
        "iat": now,
        "exp": now + 3600,
    }
    signing_input = b".".join(
        [
            _base64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _base64url(json.dumps(claims, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = credentials.signer.sign(signing_input)
    return b".".join([signing_input, _base64url(signature)]).decode("ascii")


def _credentials_token_uri(credentials) -> str:
    return getattr(credentials, "token_uri", None) or getattr(credentials, "_token_uri")


def _base64url(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def _to_firestore_fields(data: dict) -> dict:
    return {key: _to_firestore_value(value) for key, value in data.items()}


def _to_firestore_value(value):
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        if _looks_like_datetime(value):
            return {"timestampValue": value}
        return {"stringValue": value}
    if isinstance(value, list):
        return {"arrayValue": {"values": [_to_firestore_value(item) for item in value]}}
    if isinstance(value, dict):
        return {"mapValue": {"fields": _to_firestore_fields(value)}}
    return {"stringValue": str(value)}


def _from_firestore_fields(fields: dict) -> dict:
    return {key: _from_firestore_value(value) for key, value in fields.items()}


def _from_firestore_value(value: dict):
    if "nullValue" in value:
        return None
    if "booleanValue" in value:
        return value["booleanValue"]
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return value["doubleValue"]
    if "timestampValue" in value:
        return value["timestampValue"]
    if "stringValue" in value:
        return value["stringValue"]
    if "arrayValue" in value:
        return [_from_firestore_value(item) for item in value.get("arrayValue", {}).get("values", [])]
    if "mapValue" in value:
        return _from_firestore_fields(value.get("mapValue", {}).get("fields", {}))
    return None


def _looks_like_datetime(value: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}T", value))


store = NewsStore()
