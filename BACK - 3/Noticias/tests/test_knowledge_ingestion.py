import csv

from app.services.knowledge_base import clear_knowledge_cache, find_relevant_knowledge
from app.services.knowledge_ingestion import ingest_csv_to_chunks, ingest_ods_to_chunks


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


def test_finds_relevant_backend_knowledge_source(tmp_path, monkeypatch) -> None:
    source_dir = tmp_path / "knowledge_sources"
    source_dir.mkdir()
    csv_path = source_dir / "manual.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["titulo", "contenido"])
        writer.writeheader()
        writer.writerow(
            {
                "titulo": "Reglas de auditoria electoral",
                "contenido": "La auditoria electoral requiere trazabilidad, actas y contraste documental. " * 12,
            }
        )

    monkeypatch.setattr("app.services.knowledge_base._knowledge_source_dir", lambda: source_dir)
    clear_knowledge_cache()

    matches = find_relevant_knowledge("auditoria electoral actas")

    assert matches
    assert matches[0]["source_id"] == "manual"
    assert "trazabilidad" in matches[0]["text"]

    clear_knowledge_cache()


def test_ingests_ods_rows_into_chunks(tmp_path) -> None:
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    ods_path = tmp_path / "metadatos.ods"
    document = OpenDocumentSpreadsheet()
    table = Table(name="Hoja1")
    row = TableRow()
    for value in ["Variable", "Descripcion de auditoria electoral y actas documentales"]:
        cell = TableCell()
        cell.addElement(P(text=value))
        row.addElement(cell)
    table.addElement(row)
    document.spreadsheet.addElement(table)
    document.save(str(ods_path))

    chunks = ingest_ods_to_chunks(ods_path, source_id="metadatos")

    assert chunks
    assert chunks[0].source_id == "metadatos"
    assert "auditoria" in chunks[0].text
