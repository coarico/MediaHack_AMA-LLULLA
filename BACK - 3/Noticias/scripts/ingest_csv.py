import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.knowledge_ingestion import ingest_csv_to_chunks, write_chunks_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Convierte un CSV en chunks de conocimiento para RAG.")
    parser.add_argument("csv_path", help="Ruta del CSV de entrada.")
    parser.add_argument("--source-id", required=True, help="Identificador estable de la fuente.")
    parser.add_argument("--output", default="out/knowledge_chunks.jsonl", help="Archivo JSONL de salida.")
    parser.add_argument("--text-columns", nargs="*", default=None, help="Columnas que contienen texto.")
    parser.add_argument("--title-columns", nargs="*", default=None, help="Columnas que contienen titulo.")
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--overlap", type=int, default=160)
    args = parser.parse_args()

    chunks = ingest_csv_to_chunks(
        csv_path=args.csv_path,
        source_id=args.source_id,
        text_columns=args.text_columns,
        title_columns=args.title_columns,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    write_chunks_jsonl(chunks, args.output)
    print(f"Chunks generados: {len(chunks)}")
    print(f"Salida: {args.output}")


if __name__ == "__main__":
    main()
