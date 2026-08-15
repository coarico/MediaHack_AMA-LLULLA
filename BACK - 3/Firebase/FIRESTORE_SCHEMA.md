# Firestore Schema - AMA-LLU-IA

Esta base esta pensada para tres modulos:

- `noticias`: analiza una noticia insertada por URL.
- `video_audio`: recibe video/audio, transcribe y analiza el contenido.
- `auditor`: arma evidencia y reportes usando los dos tipos de analisis.

La coleccion principal es `contentAnalyses`. Auditoria debe leer de ahi para cruzar noticias, videos y audios.

## Colecciones

```text
contentAnalyses/{analysisId}
mediaAssets/{assetId}
transcripts/{transcriptId}
auditCases/{caseId}
sources/{domain}
radarMedia/{domain}
keywords/{keywordId}
knowledgeSources/{sourceId}
knowledgeChunks/{chunkId}
```

## contentAnalyses

Documento unificado para cualquier contenido analizado.

```json
{
  "id": "analysisId",
  "user_id": "uid",
  "module": "noticias",
  "content_type": "news_url",
  "visibility": "private",
  "status": "completed",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "source_input": {
    "type": "url",
    "original_url": "https://medio.com/noticia",
    "final_url": "https://medio.com/noticia",
    "submitted_title": null
  },
  "editorial_metadata": {
    "platform": "sitio_web",
    "publisher_type": "medio_comunicacion",
    "publication_date": "2026-08-14",
    "thematic_axis": "Elecciones (fraude - narcotrafico)",
    "thematic_tags": ["elecciones", "fraude", "narcotrafico"],
    "inferred": true,
    "confidence": 0.7,
    "notes": []
  },
  "content_attribution": {
    "platform_name": "Instagram",
    "platform_type": "red_social",
    "shared_by_account": "radiocentro.ec",
    "shared_by_display_name": "Radiocentro Ec",
    "publisher_name": "Radiocentro Ec",
    "publisher_handle": "radiocentro.ec",
    "publisher_type": "medio_comunicacion",
    "source_domain": "www.instagram.com",
    "explanation": "El contenido esta alojado en Instagram; la cuenta que lo comparte es radiocentro.ec."
  },
  "source_verification": {
    "status": "registered_media",
    "source_name": "El Comercio",
    "matched_domain": "elcomercio.com",
    "verification_network": null,
    "needs_additional_validation": true,
    "recommendation": "Fuente reconocida en el registro interno. Conviene contrastar si el tema es sensible o no hay cobertura relacionada.",
    "reasons": []
  },
  "information_relevance": {
    "is_relevant": true,
    "relevance_score": 82,
    "domain": "electoral",
    "definition_applied": "Informacion relevante electoral es contenido que puede afectar la comprension, decision, confianza o participacion ciudadana en un proceso electoral.",
    "subtopics": ["fraude_electoral", "narcotrafico"],
    "relation_type": "directa",
    "reasons": [],
    "how_it_relates": "Se relaciona directamente porque menciona elecciones y subtemas configurados.",
    "non_relevant_reason": null
  },
  "url_health": {
    "status": "active",
    "http_status": 200,
    "is_reachable": true,
    "is_disconnected": false,
    "redirect_count": 0,
    "warnings": []
  },
  "url_trust_assessment": {
    "is_technically_trustworthy": true,
    "level": "confiable",
    "score": 92,
    "reasons": [],
    "scope": "url_only"
  },
  "url_risk_signals": [
    {
      "signal": "shortener_url",
      "severity": "media",
      "explanation": "La URL usa un acortador y oculta el destino final."
    }
  ],
  "source_classification": {
    "is_radar_media": true,
    "communication_type": "medio_radar",
    "source_name": "Medio",
    "matched_domain": "medio.com",
    "confidence": 1,
    "explanation": "El dominio coincide con la lista Radar."
  },
  "article": {
    "title": "Titulo",
    "source_domain": "medio.com",
    "author": "Autor",
    "published_at": "2026-08-14",
    "language": "es",
    "text": "Texto limpio",
    "image_url": "https://..."
  },
  "content_quality": {
    "has_author": true,
    "has_date": true,
    "text_length": 3500,
    "has_sources": true,
    "title_body_overlap_score": 0.7,
    "quality_score": 82,
    "warnings": []
  },
  "media": null,
  "transcription": null,
  "nlp": {
    "entities": {
      "people": [],
      "organizations": [],
      "locations": []
    },
    "dates": [],
    "numbers": [],
    "keywords": [],
    "verifiable_claims": []
  },
  "related_news": [],
  "verifiable_claims": [
    {
      "claim": "Afirmacion concreta que debe verificarse.",
      "type": "evento",
      "entities": [],
      "needs_external_verification": true
    }
  ],
  "cross_source_check": {
    "related_coverage_count": 0,
    "radar_media_coverage_count": 0,
    "independent_sources_count": 0,
    "contradictions_found": false,
    "coverage_status": "not_checked",
    "notes": []
  },
  "analysis": {
    "summary": "",
    "topic": "",
    "category": "",
    "main_claims": [],
    "sentiment": {},
    "bias_analysis": {},
    "manipulation_signals": [],
    "clickbait": {},
    "credibility": {},
    "information_gaps": [],
    "missing_context": [],
    "recommendation": ""
  },
  "risk_assessment": {
    "score": 0,
    "level": "bajo",
    "fraud_or_disinformation_risk": "bajo",
    "reasons": [],
    "cannot_conclude_fraud": true
  },
  "audit": {
    "ready_for_audit": true,
    "priority": "media",
    "evidence_summary": "",
    "evidence_items": [],
    "presentation_blocks": []
  }
}
```

### Valores Permitidos

`module`:

```text
noticias
video_audio
auditor
```

`content_type`:

```text
news_url
video_file
video_url
audio_file
audio_url
transcript
mixed_case
```

`status`:

```text
pending
extracting
transcribing
analyzing
completed
failed
audit_ready
archived
```

`risk_assessment.level`:

```text
bajo
medio
alto
critico
```

## Video y Audio

Para video/audio se usa `mediaAssets` y `transcripts`.

### mediaAssets/{assetId}

```json
{
  "id": "assetId",
  "user_id": "uid",
  "analysis_id": "analysisId",
  "content_type": "video_file",
  "storage_path": "uploads/user/file.mp4",
  "source_url": null,
  "mime_type": "video/mp4",
  "duration_seconds": 92,
  "size_bytes": 10000000,
  "status": "transcribed",
  "created_at": "timestamp"
}
```

### transcripts/{transcriptId}

```json
{
  "id": "transcriptId",
  "user_id": "uid",
  "analysis_id": "analysisId",
  "asset_id": "assetId",
  "language": "es",
  "text": "Transcripcion completa",
  "segments": [
    {
      "start": 0,
      "end": 4.2,
      "text": "Fragmento",
      "speaker": "speaker_1"
    }
  ],
  "speaker_count": 1,
  "quality": {
    "confidence": 0.91,
    "warnings": []
  },
  "created_at": "timestamp"
}
```

En `contentAnalyses/{analysisId}` de video/audio:

- `source_input.type` debe ser `file` o `url`.
- `media` debe apuntar a `mediaAssets`.
- `transcription` debe apuntar a `transcripts`.
- `analysis` analiza lo dicho en la transcripcion.
- `audit.evidence_items` debe incluir citas con timestamps.

## Auditoria

### auditCases/{caseId}

Agrupa uno o varios analisis para presentacion.

```json
{
  "id": "caseId",
  "created_by": "uid",
  "title": "Caso de auditoria",
  "status": "draft",
  "analysis_ids": ["analysisId1", "analysisId2"],
  "content_types": ["news_url", "video_file"],
  "overall_risk": {
    "score": 74,
    "level": "alto",
    "main_reasons": []
  },
  "findings": [
    {
      "title": "Falta fuente primaria",
      "severity": "alta",
      "evidence_refs": []
    }
  ],
  "presentation": {
    "summary": "",
    "slides": [
      {
        "title": "Resumen",
        "bullets": [],
        "evidence_refs": []
      }
    ]
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## Campos Clave Para Auditoria

Auditoria debe priorizar:

- `source_classification`: Radar vs otros canales.
- `editorial_metadata`: plataforma, quien publica, fecha y eje tematico.
- `content_attribution`: distingue plataforma, cuenta que comparte y posible medio/noticiero.
- `source_verification`: Radar, registro interno, IFCN cuando aplique, y recomendacion de validacion.
- `information_relevance`: define si el contenido es informacion electoral relevante y que subtemas toca.
- `url_health`: link activo, roto o desconectado.
- `url_trust_assessment`: confiabilidad tecnica solo de la URL; no evalua verdad del contenido.
- `url_risk_signals`: senales tecnicas del link, sin concluir fraude.
- `content_quality`: calidad estructural del articulo.
- `cross_source_check`: si existe cobertura relacionada.
- `verifiable_claims`: afirmaciones que se deben contrastar.
- `analysis.information_gaps`: que falta en la noticia o transcripcion.
- `risk_assessment`: nivel y razones del riesgo.
- `audit.evidence_items`: evidencias concretas, URLs, citas o timestamps.
- `related_news`: contexto externo.

## radarMedia

La lista Radar puede vivir en Firestore:

```json
{
  "name": "Nombre del medio",
  "domain": "medio.com",
  "country": "CO",
  "active": true,
  "tags": ["prensa", "radio", "tv"],
  "updated_at": "timestamp"
}
```

Tambien existe una copia local editable en:

```text
BACK - 3/Noticias/data/radar_media.json
```

## RAG Desde CSV

Para que la IA use data propia sin gastar muchos tokens, el CSV se convierte primero en chunks. No se manda todo el CSV al LLM.

### knowledgeSources/{sourceId}

```json
{
  "id": "radar_csv_001",
  "name": "Base Radar CSV",
  "type": "csv",
  "status": "processed",
  "rows_count": 500,
  "chunks_count": 1200,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### knowledgeChunks/{chunkId}

```json
{
  "id": "chunkId",
  "source_id": "radar_csv_001",
  "chunk_index": 0,
  "title": "Titulo del registro",
  "text": "Fragmento limpio del CSV",
  "keywords": ["radar", "elecciones"],
  "embedding": null,
  "metadata": {
    "source_file": "data.csv",
    "row_index": 0
  },
  "status": "ready_for_embedding"
}
```

Flujo recomendado:

```text
CSV -> chunks -> keywords locales -> embeddings locales o baratos -> top-k relevante -> LLM solo recibe fragmentos relevantes
```
