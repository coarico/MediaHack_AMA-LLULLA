import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TEXT_COLUMNS = ("text", "content", "contenido", "descripcion", "description", "body", "noticia")
DEFAULT_TITLE_COLUMNS = ("title", "titulo", "name", "nombre")


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    source_id: str
    chunk_index: int
    title: str | None
    text: str
    keywords: list[str]
    metadata: dict

    def to_firestore_dict(self) -> dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "text": self.text,
            "keywords": self.keywords,
            "metadata": self.metadata,
            "embedding": None,
            "status": "ready_for_embedding",
        }


def ingest_csv_to_chunks(
    csv_path: str | Path,
    source_id: str,
    text_columns: list[str] | None = None,
    title_columns: list[str] | None = None,
    chunk_size: int = 1200,
    overlap: int = 160,
) -> list[KnowledgeChunk]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el CSV: {path}")

    chunks: list[KnowledgeChunk] = []
    selected_text_columns = [column.lower() for column in (text_columns or DEFAULT_TEXT_COLUMNS)]
    selected_title_columns = [column.lower() for column in (title_columns or DEFAULT_TITLE_COLUMNS)]

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("El CSV no tiene encabezados.")

        for row_index, row in enumerate(reader):
            normalized_row = {key.lower().strip(): (value or "").strip() for key, value in row.items() if key}
            text = _pick_text(normalized_row, selected_text_columns)
            if not text:
                continue
            title = _pick_first(normalized_row, selected_title_columns)
            metadata = {
                "source_file": path.name,
                "row_index": row_index,
                "raw": normalized_row,
            }
            for chunk_index, chunk_text in enumerate(_chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
                chunk_id = _stable_id(source_id, row_index, chunk_index, chunk_text)
                chunks.append(
                    KnowledgeChunk(
                        id=chunk_id,
                        source_id=source_id,
                        chunk_index=chunk_index,
                        title=title,
                        text=chunk_text,
                        keywords=_extract_keywords(chunk_text),
                        metadata=metadata,
                    )
                )
    return chunks


def write_chunks_jsonl(chunks: list[KnowledgeChunk], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk.to_firestore_dict(), ensure_ascii=False) + "\n")


def _pick_text(row: dict[str, str], text_columns: list[str]) -> str:
    values = [row[column] for column in text_columns if row.get(column)]
    if values:
        return "\n\n".join(values).strip()
    return "\n\n".join(value for value in row.values() if len(value) > 40).strip()


def _pick_first(row: dict[str, str], columns: list[str]) -> str | None:
    for column in columns:
        if row.get(column):
            return row[column]
    return None


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= chunk_size:
        return [clean]

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        if end < len(clean):
            boundary = clean.rfind(". ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunks.append(clean[start:end].strip())
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _extract_keywords(text: str, limit: int = 12) -> list[str]:
    stopwords = {
        "para",
        "como",
        "sobre",
        "entre",
        "desde",
        "hasta",
        "tambien",
        "también",
        "cuando",
        "donde",
        "porque",
        "esta",
        "este",
        "estos",
        "estas",
        "segun",
        "según",
        "noticia",
        "contenido",
    }
    words = re.findall(r"\b[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ0-9_-]{3,}\b", text.lower())
    counts: dict[str, int] = {}
    for word in words:
        if word not in stopwords:
            counts[word] = counts.get(word, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def _stable_id(source_id: str, row_index: int, chunk_index: int, text: str) -> str:
    digest = hashlib.sha256(f"{source_id}:{row_index}:{chunk_index}:{text[:120]}".encode("utf-8")).hexdigest()
    return digest[:24]

