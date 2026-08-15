import json
import re
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.services.knowledge_ingestion import (
    KnowledgeChunk,
    ingest_csv_to_chunks,
    ingest_ods_to_chunks,
    ingest_pdf_to_chunks,
)


SUPPORTED_EXTENSIONS = {".csv", ".ods", ".pdf"}


def find_relevant_knowledge(query_text: str, limit: int | None = None) -> list[dict]:
    chunks = load_knowledge_chunks()
    if not chunks:
        return []

    query_terms = _terms(query_text)
    if not query_terms:
        return []

    scored = []
    for chunk in chunks:
        chunk_terms = set(chunk.keywords) | _terms(chunk.title or "") | _terms(chunk.text)
        score = len(query_terms & chunk_terms)
        if score:
            scored.append((score, len(chunk.text), chunk))

    selected = sorted(scored, key=lambda item: (-item[0], item[1]))[: limit or settings.knowledge_context_limit]
    return [
        {
            "source_id": chunk.source_id,
            "title": chunk.title,
            "text": chunk.text[: settings.knowledge_context_chunk_chars],
            "keywords": chunk.keywords[:8],
            "metadata": chunk.metadata,
        }
        for _, _, chunk in selected
    ]


@lru_cache(maxsize=1)
def load_knowledge_chunks() -> tuple[KnowledgeChunk, ...]:
    source_dir = _knowledge_source_dir()
    if not source_dir.exists():
        return ()

    chunks: list[KnowledgeChunk] = []
    for path in sorted(source_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        source_id = _source_id(path)
        try:
            if path.suffix.lower() == ".csv":
                chunks.extend(ingest_csv_to_chunks(path, source_id=source_id))
            elif path.suffix.lower() == ".ods":
                chunks.extend(ingest_ods_to_chunks(path, source_id=source_id))
            elif path.suffix.lower() == ".pdf":
                chunks.extend(ingest_pdf_to_chunks(path, source_id=source_id))
        except Exception as exc:
            chunks.append(
                KnowledgeChunk(
                    id=f"{source_id}_error",
                    source_id=source_id,
                    chunk_index=0,
                    title=path.name,
                    text=f"No se pudo cargar esta fuente de conocimiento: {exc}",
                    keywords=[],
                    metadata={"source_file": path.name, "error": str(exc)},
                )
            )
    return tuple(chunks)


def clear_knowledge_cache() -> None:
    load_knowledge_chunks.cache_clear()


def _knowledge_source_dir() -> Path:
    configured = Path(settings.knowledge_sources_dir)
    if configured.is_absolute():
        return configured
    return Path(__file__).resolve().parents[2] / configured


def _source_id(path: Path) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", path.stem).strip("_").lower()
    return safe_name or "knowledge_source"


def _terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"\b[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9_-]{4,}\b", (text or "").lower())
        if word not in {"para", "como", "sobre", "entre", "desde", "hasta", "esta", "este", "estos", "estas"}
    }
