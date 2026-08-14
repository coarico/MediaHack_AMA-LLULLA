# Modulo de Video (Programador 2)

Detecta si un video fue generado/manipulado por IA combinando:

- **ML**: clasificador de imagenes real-vs-fake (`app/ml/`), corrido por frame
  sobre el video y agregado a un score de video.
- **Heuristicas OpenCV** (`app/services/video_analyzer.py`): jitter de la cara
  detectada entre frames, varianza de nitidez (artefactos de compresion) y
  parpadeo/flicker de histograma de color entre frames consecutivos.

Score final = `0.65 * ml_score + 0.35 * heuristic_score` (ver constantes
`ML_WEIGHT` / `HEURISTIC_WEIGHT` en `video_analyzer.py`).

## Que existe hoy

```
app/
  ml/
    model_loader.py   # carga el modelo HF (lazy) + modo mock para tests
    inference.py       # clasifica frames y agrega scores
  services/
    video_analyzer.py  # extraccion de frames, heuristicas, orquestacion
  models/
    video_schemas.py   # Pydantic: request/response del endpoint de video
  api/
    video.py           # router FastAPI: POST /api/v1/analyze/video (async + job)
models/
  face_detection_yunet_2023mar.onnx  # detector facial (OpenCV Zoo, MIT)
  README.md
tests/
  conftest.py           # app FastAPI minima + fixture de video sintetico
  test_video.py          # unit tests de analyzer/ml
  test_api.py             # integration tests del endpoint
requirements-video.txt
```

**No toque** `app/models/schemas.py`, `app/config.py`, `main.py` ni
`requirements.txt` porque son compartidos / responsabilidad del Programador 1
(audio + setup base). `app/models/video_schemas.py` es un archivo separado
para no pisar su `schemas.py`.

## Como correr

```bash
pip install -r requirements-video.txt
VIDEO_ML_MOCK=1 pytest tests/ -v      # sin descargar pesos del clasificador
```

Sin `VIDEO_ML_MOCK=1`, la primera llamada descarga el modelo de Hugging Face
(`dima806/deepfake_vs_real_image_detection`, ver `models/README.md`).

## Punto de integracion pendiente

Cuando exista `main.py` (Programador 1), montar el router asi:

```python
from app.api.video import router as video_router
app.include_router(video_router)
```

El endpoint es asincrono con seguimiento de progreso:

1. `POST /api/v1/analyze/video` (multipart, campo `file`) -> `202` con `job_id`
2. `GET /api/v1/analyze/video/{job_id}` -> `status` (`queued|processing|done|failed`),
   `progress` (0-100) y `result` cuando `status == "done"`

Tambien falta fusionar `requirements-video.txt` dentro del `requirements.txt`
compartido, y unificar `app/models/video_schemas.py` con `app/models/schemas.py`
cuando ambos existan.
