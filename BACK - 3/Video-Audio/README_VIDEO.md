# Modulo de Video (Programador 2)

Ya integrado en `app/main.py`. Detecta si un video fue generado/manipulado
por IA combinando:

- **ML**: clasificador de imagenes real-vs-fake (`app/ml/`), corrido por frame
  sobre el video y agregado a un score de video.
- **Heuristicas OpenCV** (`app/services/video_analyzer.py`): jitter de la cara
  detectada entre frames (YuNet), varianza de nitidez (artefactos de
  compresion) y parpadeo/flicker de histograma de color entre frames
  consecutivos.

Score final = `0.65 * ml_score + 0.35 * promedio(heuristicas)` (constantes
`ML_WEIGHT` / `HEURISTIC_WEIGHT` en `video_analyzer.py`). Sigue exactamente el
mismo contrato que `AudioAnalyzer`: una clase `VideoAnalyzer` con
`async def analyze(file_path) -> AnalysisResponse`, usando los schemas
compartidos de `app/models/schemas.py` (`AnalysisResponse`,
`VideoAnalysisDetails`, `MediaMetadata`, `ArtifactDetection`).

## Archivos de este modulo

```
app/
  ml/
    model_loader.py    # carga el modelo HF (lazy) + modo mock para tests
    inference.py        # clasifica frames y agrega scores
  services/
    video_analyzer.py   # extraccion de frames, heuristicas, VideoAnalyzer
models/
  face_detection_yunet_2023mar.onnx  # detector facial (OpenCV Zoo, MIT)
  README.md
tests/
  conftest.py            # TestClient de app.main + fixture de video sintetico
  test_video.py           # unit tests de analyzer/ml
  test_api.py              # integration tests del endpoint /analyze/video
```

## Endpoints (en `app/main.py`)

- `POST /api/v1/analyze/video` (multipart, campo `file`) -> `AnalysisResponse`
- `POST /api/v1/analyze/url` -> tambien detecta y analiza video si la URL
  apunta a un archivo de video (extendido para soportar ambos tipos)

## Como correr

```bash
pip install -r requirements.txt
VIDEO_ML_MOCK=1 pytest tests/ -v      # sin descargar pesos del clasificador
```

Sin `VIDEO_ML_MOCK=1`, la primera llamada descarga el modelo de Hugging Face
(`dima806/deepfake_vs_real_image_detection`, ver `models/README.md`).

## Variables de entorno propias de este modulo

- `VIDEO_ML_MODEL_ID` — modelo HF a usar (default: `dima806/deepfake_vs_real_image_detection`)
- `VIDEO_ML_DEVICE` — `cpu` (default) o indice de GPU
- `VIDEO_ML_MOCK` — `1` para predictor determinista sin descargar pesos (tests/CI)
- `VIDEO_FACE_DETECTOR_PATH` — ruta al `.onnx` de YuNet (default: `models/face_detection_yunet_2023mar.onnx`)
