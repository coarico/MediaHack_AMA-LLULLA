import csv

from app.services.knowledge_ingestion import ingest_csv_to_chunks


def test_ingests_csv_rows_into_chunks(tmp_path) -> None:
    csv_path = tmp_path / "data.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["titulo", "contenido"])
        writer.writeheader()
        writer.writerow(
            {
                "titulo": "Reporte electoral",
                "contenido": "El reporte menciona auditoria, elecciones y verificacion de fuentes. " * 20,
            }
        )

    chunks = ingest_csv_to_chunks(csv_path, source_id="radar_csv")

    assert chunks
    assert chunks[0].source_id == "radar_csv"
    assert chunks[0].title == "Reporte electoral"
    assert "reporte" in chunks[0].keywords

