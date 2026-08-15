# AMA-LLU-IA Noticias API

Backend para analizar noticias mediante un link, generar palabras clave y buscar noticias relacionadas.

## Stack

- FastAPI
- Firebase Admin SDK + Firestore
- Trafilatura para extraccion de articulos
- OpenAI Structured Outputs para analisis profundo
- GDELT + DuckDuckGo para noticias relacionadas gratuitas

## Instalacion

```bash
cd "BACK - 3/Noticias"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Configura `.env` con las claves disponibles. El servicio puede correr sin claves, pero:

- sin `OPENAI_API_KEY` usa analisis heuristico local
- sin Firebase guarda solo en memoria
- GDELT no requiere API key; si no encuentra resultados, usa DuckDuckGo como respaldo

## Ejecutar

```bash
uvicorn app.main:app --reload --port 8001
```

Healthcheck:

```text
GET http://localhost:8001/health
```

Analizar noticia:

```text
POST http://localhost:8001/api/v1/noticias/analyze
Content-Type: application/json

{
  "url": "https://ejemplo.com/noticia"
}
```

## Respuesta pensada para el frontend

El frontend puede mostrar directamente:

- `source_input.original_url`
- `source_input.final_url`
- `editorial_metadata.platform`
- `editorial_metadata.publisher_type`
- `editorial_metadata.publication_date`
- `editorial_metadata.thematic_axis`
- `content_attribution.shared_by_account`
- `content_attribution.publisher_name`
- `content_attribution.publisher_type`
- `source_verification.status`
- `source_verification.needs_additional_validation`
- `source_verification.recommendation`
- `information_relevance.is_relevant`
- `information_relevance.subtopics`
- `information_relevance.relation_type`
- `information_relevance.relevance_score`
- `url_health.status`
- `url_health.is_disconnected`
- `url_trust_assessment.level`
- `url_trust_assessment.score`
- `url_risk_signals`
- `content_quality`
- `analysis.summary`
- `analysis.keywords`
- `source_classification.is_radar_media`
- `source_classification.communication_type`
- `source_classification.source_name`
- `analysis.main_claims`
- `analysis.bias_analysis`
- `analysis.clickbait`
- `analysis.credibility`
- `analysis.information_gaps`
- `analysis.missing_context`
- `risk_assessment.level`
- `risk_assessment.reasons`
- `verifiable_claims`
- `cross_source_check`
- `audit.evidence_summary`
- `audit.evidence_items`
- `related_news`

`analysis.information_gaps` indica que le falta a la noticia para estar mejor sustentada. Cada elemento trae:

- `missing_item`: dato, fuente, documento o contexto faltante
- `why_it_matters`: por que afecta la calidad de la informacion
- `suggested_verification`: que deberia buscarse para verificarlo
- `priority`: `baja`, `media` o `alta`

## Firebase

Los analisis se guardan en la coleccion unificada:

```text
contentAnalyses/{analysisId}
```

Cada documento contiene `module`, `content_type`, `source_input`, `editorial_metadata`, `content_attribution`, `source_verification`, `information_relevance`, `url_health`, `url_trust_assessment`, `url_risk_signals`, `article`, `content_quality`, `source_classification`, `analysis`, `verifiable_claims`, `cross_source_check`, `risk_assessment`, `audit`, `related_news`, `created_at`, `updated_at` y `status`.

## Definicion De Informacion Relevante Electoral

La taxonomia editable esta en:

```text
data/election_taxonomy.json
```

El backend considera relevante electoral el contenido que puede afectar la comprension, decision, confianza o participacion ciudadana en un proceso electoral.

Subtemas iniciales:

- fraude electoral
- narcotrafico y campanas
- candidatos y campanas
- autoridad electoral
- encuestas
- resultados electorales
- violencia y seguridad electoral
- normas y calendario electoral
- desinformacion electoral

El request tambien puede recibir metadata editorial opcional:

```json
{
  "url": "https://medio.com/noticia",
  "platform": "sitio_web",
  "publisher_type": "medio_comunicacion",
  "publication_date": "14/08/2026",
  "thematic_axis": "Elecciones (fraude - narcotrafico)"
}
```

Si no llega, el backend intenta inferirla.

El contrato general de Firebase para Noticias, Video-Audio y Auditor esta en:

```text
../Firebase/FIRESTORE_SCHEMA.md
```

## Lista Radar

El clasificador de fuente lee:

```text
data/radar_media.json
```

Formato:

```json
{
  "media": [
    {
      "name": "Nombre del medio",
      "domain": "medio.com"
    }
  ]
}
```

Si el dominio coincide con esa lista, devuelve:

```json
{
  "is_radar_media": true,
  "communication_type": "medio_radar"
}
```

Si no coincide, lo clasifica como `medio_no_radar`, `red_social`, `blog`, `gobierno`, `institucion`, `empresa`, `ong`, `plataforma_video`, `otro` o `desconocido`.

## CSV Para RAG Sin Gastar Muchos Tokens

El CSV no se envia completo al modelo. Primero se convierte a chunks locales:

```bash
python scripts/ingest_csv.py data/mi_base.csv --source-id radar_csv_001 --output out/knowledge_chunks.jsonl
```

Si tus columnas tienen nombres especificos:

```bash
python scripts/ingest_csv.py data/mi_base.csv --source-id radar_csv_001 --text-columns contenido descripcion --title-columns titulo
```

La salida `JSONL` se puede subir a Firestore en `knowledgeChunks`. Luego el analisis busca solo los chunks relevantes y manda al LLM un contexto corto.
