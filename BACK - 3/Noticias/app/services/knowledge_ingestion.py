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


def ingest_pdf_to_chunks(
    pdf_path: str | Path,
    source_id: str,
    chunk_size: int = 1200,
    overlap: int = 160,
) -> list[KnowledgeChunk]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el PDF: {path}")

    text_by_page = _extract_pdf_pages(path)
    chunks: list[KnowledgeChunk] = []
    for page_index, page_text in enumerate(text_by_page):
        if not page_text.strip():
            continue
        metadata = {
            "source_file": path.name,
            "page_index": page_index,
            "page_number": page_index + 1,
        }
        for chunk_index, chunk_text in enumerate(_chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)):
            chunk_id = _stable_id(source_id, page_index, chunk_index, chunk_text)
            chunks.append(
                KnowledgeChunk(
                    id=chunk_id,
                    source_id=source_id,
                    chunk_index=chunk_index,
                    title=path.stem,
                    text=chunk_text,
                    keywords=_extract_keywords(chunk_text),
                    metadata=metadata,
                )
            )
    return chunks


def ingest_ods_to_chunks(
    ods_path: str | Path,
    source_id: str,
    chunk_size: int = 1200,
    overlap: int = 160,
) -> list[KnowledgeChunk]:
    path = Path(ods_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el ODS: {path}")

    rows = _extract_ods_rows(path)
    chunks: list[KnowledgeChunk] = []
    for row_index, row in enumerate(rows):
        text = " | ".join(value for value in row if value)
        if len(text) < 20:
            continue
        title = row[0] if row else path.stem
        metadata = {
            "source_file": path.name,
            "row_index": row_index,
            "raw": row,
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


def _extract_pdf_pages(path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Para subir PDF instala pypdf en requirements.txt.") from exc

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    if not any(page.strip() for page in pages):
        raise ValueError("No se pudo extraer texto del PDF. Puede ser escaneado/imagen.")
    return pages


def _extract_ods_rows(path: Path) -> list[list[str]]:
    try:
        from odf.opendocument import load
        from odf.table import Table, TableCell, TableRow
        from odf.text import P
    except ImportError as exc:
        raise RuntimeError("Para subir ODS instala odfpy en requirements.txt.") from exc

    document = load(str(path))
    rows: list[list[str]] = []
    for table in document.spreadsheet.getElementsByType(Table):
        for row in table.getElementsByType(TableRow):
            values: list[str] = []
            for cell in row.getElementsByType(TableCell):
                repeat = int(cell.getAttribute("numbercolumnsrepeated") or 1)
                text = " ".join(
                    str(node.firstChild.data)
                    for node in cell.getElementsByType(P)
                    if node.firstChild
                ).strip()
                values.extend([text] * min(repeat, 20))
            if any(values):
                rows.append(values)
    if not rows:
        raise ValueError("No se pudo extraer texto del ODS.")
    return rows


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
